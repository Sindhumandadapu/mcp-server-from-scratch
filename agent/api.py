
import asyncio
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter

from agent.main import (
    create_llm,
    SYSTEM_PROMPT,
    SECURITY_PROMPT,
    MCP_SERVER_URL,
)

from agent.memory import ConversationMemory
from agent.tool_audit import ToolAuditCallback


# =========================================================
# 1. APPLICATION LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize the LLM, MCP connection, agent and memory
    when FastAPI starts.

    Keep the MCP connection alive until FastAPI shuts down.
    """

    print("\nInitializing SmartTools FastAPI application...")

    llm = create_llm()

    memory = ConversationMemory()

    print("Connecting to MCP server...")

    async with MCPAdapter(MCP_SERVER_URL) as adapter:

        tools = await adapter.list_tools()

        if not tools:
            raise RuntimeError("No MCP tools were discovered.")

        print(f"Discovered {len(tools)} MCP tools.")

        # Combine the normal agent instructions and security instructions.
        combined_system_prompt = (
            SYSTEM_PROMPT
            + "\n\n"
            + SECURITY_PROMPT
        )

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=combined_system_prompt,
            name="smarttools_agent",
        )

        app.state.agent = agent
        app.state.memory = memory
        app.state.tools = tools

        # Separate lock for each conversation session.
        app.state.session_locks = {}

        print("Prompt injection defense instructions enabled.")
        print("MCP tool-call auditing enabled.")
        print("SmartTools FastAPI application is ready.")

        yield

    print("SmartTools FastAPI application stopped.")


# =========================================================
# 2. FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="SmartTools AI API",
    description=(
        "REST API for the SmartTools MCP-powered "
        "LangChain AI agent."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# =========================================================
# 3. CORS CONFIGURATION
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


# =========================================================
# 4. REQUEST AND RESPONSE MODELS
# =========================================================

class ChatRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=10000,
        description="User message",
    )

    session_id: str = Field(
        default="default",
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Conversation session identifier",
    )


class ChatResponse(BaseModel):

    session_id: str

    response: str

    status: str = "success"


# =========================================================
# 5. RESPONSE EXTRACTION
# =========================================================

def extract_response_content(content):
    """Convert LangChain message content into text."""

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, dict):

                text_part = item.get("text")

                if text_part:
                    parts.append(text_part)

            else:
                parts.append(str(item))

        return "\n".join(parts)

    return str(content)


# =========================================================
# 6. ERROR DIAGNOSTICS
# =========================================================

def log_chat_error(exc):
    """
    Print useful provider error details without printing
    environment variables, API keys or request headers.
    """

    print("\n" + "=" * 65)
    print("SMARTTOOLS CHAT ERROR DETAILS")
    print("=" * 65)

    print("Error type:", type(exc).__name__)
    print("Error message:", repr(exc))

    error_body = getattr(exc, "body", None)

    if error_body is not None:

        print("\nProvider error body:")
        print(repr(error_body))

        if isinstance(error_body, dict):

            # Support both top-level and nested Groq error fields.
            error_details = error_body.get("error", error_body)

            if isinstance(error_details, dict):

                failed_generation = error_details.get(
                    "failed_generation"
                )

                if failed_generation is not None:
                    print("\nGroq failed generation:")
                    print(repr(failed_generation))

    else:
        print("\nNo structured error body was available.")

    print("\nPython traceback:")
    traceback.print_exc()

    print("=" * 65 + "\n")


# =========================================================
# 7. SESSION LOCK
# =========================================================

def get_session_lock(session_id: str):

    locks = app.state.session_locks

    if session_id not in locks:
        locks[session_id] = asyncio.Lock()

    return locks[session_id]


# =========================================================
# 8. ROOT ENDPOINT
# =========================================================

@app.get("/")
async def root():

    return {
        "application": "SmartTools AI API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
    }


# =========================================================
# 9. HEALTH CHECK
# =========================================================

@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "agent_initialized": hasattr(
            app.state,
            "agent",
        ),
        "mcp_tools": len(app.state.tools),
    }


# =========================================================
# 10. LIST MCP TOOLS
# =========================================================

@app.get("/tools")
async def list_tools():

    tools = app.state.tools

    return {
        "total_tools": len(tools),
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in tools
        ],
    }


# =========================================================
# 11. CHAT ENDPOINT
# =========================================================

@app.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(request: ChatRequest):

    session_id = request.session_id

    user_message = request.message.strip()

    if not user_message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    lock = get_session_lock(session_id)

    async with lock:

        try:

            memory = app.state.memory

            # Load previous conversation.
            conversation_history = memory.load(
                session_id
            )

            # Add the current user message.
            conversation_history.append(
                {
                    "role": "user",
                    "content": user_message,
                }
            )

            # Create an audit callback for this request.
            audit_callback = ToolAuditCallback(
                session_id=session_id
            )

            # Execute the LangChain agent with tool auditing.
            result = await app.state.agent.ainvoke(
                {
                    "messages": conversation_history
                },
                config={
                    "callbacks": [audit_callback],
                },
            )

            updated_history = result["messages"]

            if not updated_history:

                raise RuntimeError(
                    "Agent returned an empty response."
                )

            final_message = updated_history[-1]

            answer = extract_response_content(
                final_message.content
            )

            if not answer.strip():

                raise RuntimeError(
                    "Agent returned an empty text response."
                )

            # Persist successful conversation.
            memory.save(
                updated_history,
                session_id,
            )

            return ChatResponse(
                session_id=session_id,
                response=answer,
                status="success",
            )

        except Exception as exc:

            # Print detailed diagnostic information.
            print(
                f"Chat request failed for session {session_id}"
            )

            log_chat_error(exc)

            raise HTTPException(
                status_code=502,
                detail=(
                    "The AI agent could not process "
                    "your request. Check the server logs."
                ),
            ) from exc


# =========================================================
# 12. GET CONVERSATION HISTORY
# =========================================================

@app.get("/history/{session_id}")
async def get_history(session_id: str):

    if not session_id or len(session_id) > 64:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID.",
        )

    lock = get_session_lock(session_id)

    async with lock:

        messages = app.state.memory.load(
            session_id
        )

        visible_messages = []

        for message in messages:

            if message.type == "human":
                role = "user"

            elif message.type == "ai":
                role = "assistant"

            else:
                continue

            content = extract_response_content(
                message.content
            )

            if not content:
                continue

            visible_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return {
            "session_id": session_id,
            "total_messages": len(visible_messages),
            "messages": visible_messages,
        }


# =========================================================
# 13. DELETE CONVERSATION HISTORY
# =========================================================

@app.delete("/history/{session_id}")
async def delete_history(session_id: str):

    if not session_id or len(session_id) > 64:

        raise HTTPException(
            status_code=400,
            detail="Invalid session ID.",
        )

    lock = get_session_lock(session_id)

    async with lock:

        app.state.memory.clear(session_id)

        return {
            "session_id": session_id,
            "status": "success",
            "message": "Conversation history cleared.",
        }
