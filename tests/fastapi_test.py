import uuid

import httpx
import pytest


BASE_URL = "http://127.0.0.1:8001"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fastapi_application():

    try:
        async with httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=90
        ) as client:

            # Health check
            response = await client.get("/health")

            assert response.status_code == 200

            health = response.json()

            assert health["status"] == "healthy"
            assert health["mcp_tools"] == 12

            # Tool discovery
            response = await client.get("/tools")

            assert response.status_code == 200

            tools = response.json()

            assert tools["total_tools"] == 12

            # Chat
            session_id = f"test_{uuid.uuid4().hex[:12]}"

            response = await client.post(
                "/chat",
                json={
                    "session_id": session_id,
                    "message": "Calculate 12 multiplied by 8."
                }
            )

            assert response.status_code == 200, response.text

            chat = response.json()

            assert chat["status"] == "success"
            assert chat["response"]

            # Conversation history
            response = await client.get(
                f"/history/{session_id}"
            )

            assert response.status_code == 200

            history = response.json()

            assert history["total_messages"] >= 2

            # Delete conversation
            response = await client.delete(
                f"/history/{session_id}"
            )

            assert response.status_code == 200

            # Verify deletion
            response = await client.get(
                f"/history/{session_id}"
            )

            assert response.json()["total_messages"] == 0

    except httpx.ConnectError:
        pytest.skip("FastAPI server is not running on port 8001.")