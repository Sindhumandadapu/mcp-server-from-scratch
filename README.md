# MCP Server From Scratch

A custom **Model Context Protocol (MCP) server** built from scratch using Python, exposing multiple tools that an AI agent can discover and execute. The project integrates MCP tools with an AI agent powered by LangChain and Groq, along with conversational memory, API integrations, database operations, file handling, and a React frontend.

## Overview

The goal of this project is to understand and implement the Model Context Protocol from the ground up — creating an MCP server, defining tools, exposing them through MCP, and connecting the server to an AI agent that can intelligently select and use tools based on user requests.

The AI agent interacts with the custom MCP server to perform tasks such as calculations, file searches, database queries, API calls, weather lookups, and currency conversions.

## Architecture

```text
                User
                 |
                 v
         React Frontend
                 |
                 v
          FastAPI Backend
                 |
                 v
             AI Agent
        (LangChain + Groq)
                 |
                 v
          MCP Client Adapter
                 |
                 v
        Custom MCP Server
         Built from Scratch
                 |
       +---------+----------+
       |         |          |
       v         v          v
     Tools    Database    External APIs
```

## Features

- **Custom MCP Server** – Built from scratch using Python and MCP.
- **AI Agent Integration** – Agent powered by LangChain and Groq.
- **Tool Discovery and Execution** – AI agent discovers and invokes MCP tools dynamically.
- **12 MCP Tools** – Tools for calculations, file operations, database access, and API integrations.
- **Conversational Memory** – Maintains conversation context using SQLite.
- **Database Operations** – Schema inspection and read-only SQL querying.
- **File Operations** – Search and read supported files within a restricted resources directory.
- **API Integrations** – Weather information, currency conversion, and controlled HTTP requests.
- **Security Controls** – Restricted file access, read-only database queries, API host allowlisting, and prompt-injection defenses.
- **Tool Audit Logging** – Tracks tool execution events, status, and execution duration.
- **REST API** – FastAPI backend for application integration.
- **Web Interface** – React frontend built with Vite.
- **Automated Testing** – Unit and integration tests using pytest.

## MCP Tools

| Category | Tools |
|---|---|
| Calculator | `add`, `subtract`, `multiply`, `divide` |
| File Operations | `search_files`, `read_file` |
| Database | `list_tables`, `get_table_schema`, `query_database` |
| API & Utilities | `get_weather`, `convert_currency`, `make_api_request` |

## Tech Stack

**Backend & AI**
- Python
- Model Context Protocol (MCP)
- LangChain
- Groq
- FastAPI

**Frontend**
- React
- Vite
- JavaScript

**Database & Storage**
- SQLite
- JSONL audit logs

**Testing & Development**
- pytest
- Git
- GitHub

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js and npm
- Groq API key

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/mcp-server-from-scratch.git
cd mcp-server-from-scratch
```

### 2. Set Up Python Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace `your_groq_api_key` with your actual Groq API key.

**Never commit your `.env` file or API keys to GitHub.**

### 5. Run the MCP Server

**HTTP mode**

```bash
python -m server.http_server
```

**STDIO mode**

```bash
python -m server.stdio_server
```

### 6. Run the Backend API

```bash
python -m agent.api
```

### 7. Run the Frontend

Open another terminal:

```bash
cd client
npm install
npm run dev
```

Open the frontend URL displayed by Vite in your browser.

## Running Tests

Run the complete test suite:

```bash
python -m pytest tests -v
```

Run tests excluding integration tests:

```bash
python -m pytest tests -v -m "not integration"
```

Run integration tests:

```bash
python -m pytest tests -v -m integration
```

Generate a coverage report:

```bash
python -m pytest tests -v --cov=agent --cov=server --cov=tools --cov-branch --cov-report=term-missing --cov-report=html
```

## Security

The project includes several security-focused measures:

- Restricted file access to permitted directories and file types.
- Protection against path traversal.
- Read-only database query restrictions.
- API host allowlisting.
- HTTP request restrictions and timeouts.
- Prompt-injection defense for untrusted content.
- Tool execution audit logging without recording sensitive tool arguments or results.

## Learning Objectives

This project explores:

- How the Model Context Protocol works.
- How to create an MCP server from scratch.
- How to expose tools through MCP.
- How MCP clients discover and call tools.
- How to connect MCP servers to AI agents.
- Tool calling and agent orchestration.
- Conversational memory.
- Security considerations in AI tool execution.
- Testing MCP servers and integrations.

## Future Improvements

- Improve automated test coverage.
- Add additional MCP tools.
- Enhance security and error handling.
- Improve agent observability.
- Expand frontend functionality.
- Explore multi-agent workflows.

---

**Built as a hands-on project to learn and implement the Model Context Protocol from scratch.**
