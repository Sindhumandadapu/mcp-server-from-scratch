
import { useEffect, useRef, useState } from "react";
import {
  Activity,
  Bot,
  CheckCircle2,
  ChevronDown,
  Code2,
  Database,
  FileSearch,
  History,
  LoaderCircle,
  MessageSquare,
  Plus,
  Send,
  Server,
  ShieldCheck,
  Trash2,
  Wrench,
  X,
  Calculator,
  CloudSun,
  ArrowLeftRight,
  Menu,
  Sparkles,
} from "lucide-react";

import {
  checkHealth,
  getTools,
  sendMessage,
  getHistory,
  deleteHistory,
} from "./api";

import "./App.css";

const STORAGE_KEY = "smarttools_sessions";
const ACTIVE_KEY = "smarttools_active_session";

function createSession() {
  return {
    id: `chat_${Date.now().toString(36)}_${Math.random()
      .toString(36)
      .slice(2, 8)}`,
    title: "New conversation",
    updatedAt: Date.now(),
  };
}

function readSessions() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value)
      ? value.filter(
          (session) =>
            session &&
            typeof session.id === "string" &&
            /^[A-Za-z0-9_-]{1,64}$/.test(session.id)
        )
      : [];
  } catch {
    return [];
  }
}

function getToolIcon(name) {
  const value = name.toLowerCase();

  if (value.includes("calculator")) return Calculator;
  if (value.includes("file")) return FileSearch;
  if (value.includes("database") || value.includes("table")) return Database;
  if (value.includes("weather")) return CloudSun;
  if (value.includes("currency")) return ArrowLeftRight;

  return Wrench;
}

function App() {
  const [sessions, setSessions] = useState(readSessions);

  const [activeSessionId, setActiveSessionId] = useState(() => {
    const savedSessions = readSessions();
    const savedId = localStorage.getItem(ACTIVE_KEY);

    return savedSessions.some((item) => item.id === savedId)
      ? savedId
      : savedSessions[0]?.id || "";
  });

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const [health, setHealth] = useState(null);
  const [tools, setTools] = useState([]);

  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState("");

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(true);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Create an initial conversation when necessary.
  useEffect(() => {
    if (sessions.length === 0) {
      const session = createSession();
      setSessions([session]);
      setActiveSessionId(session.id);
      return;
    }

    if (!sessions.some((item) => item.id === activeSessionId)) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId]);

  // Persist the session index in this browser.
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    if (activeSessionId) {
      localStorage.setItem(ACTIVE_KEY, activeSessionId);
    }
  }, [activeSessionId]);

  // Load backend status and available MCP tools.
  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const [healthResult, toolsResult] = await Promise.all([
          checkHealth(),
          getTools(),
        ]);

        if (!cancelled) {
          setHealth(healthResult);
          setTools(toolsResult.tools || []);
        }
      } catch {
        if (!cancelled) {
          setHealth(null);
          setError(
            "Cannot connect to FastAPI. Make sure both backend servers are running."
          );
        }
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, []);

  // Restore conversation messages whenever the session changes.
  useEffect(() => {
    if (!activeSessionId) return;

    let cancelled = false;

    async function loadConversation() {
      setMessages([]);
      setError("");
      setLoadingHistory(true);

      try {
        const result = await getHistory(activeSessionId);

        if (!cancelled) {
          setMessages(
            (result.messages || []).map((message, index) => ({
              id: `${activeSessionId}_${index}`,
              role: message.role,
              content: message.content,
            }))
          );
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load conversation history.");
        }
      } finally {
        if (!cancelled) {
          setLoadingHistory(false);
        }
      }
    }

    loadConversation();

    return () => {
      cancelled = true;
    };
  }, [activeSessionId]);

  // Scroll to the newest message.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  async function handleSend(event) {
    event.preventDefault();

    const message = input.trim();

    if (!message || loading || !activeSessionId) return;

    const sessionId = activeSessionId;

    const userMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: message,
    };

    setInput("");
    setError("");
    setMessages((previous) => [...previous, userMessage]);
    setLoading(true);

    setSessions((previous) =>
      previous.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              title:
                session.title === "New conversation"
                  ? message.slice(0, 38)
                  : session.title,
              updatedAt: Date.now(),
            }
          : session
      )
    );

    try {
      const result = await sendMessage(message, sessionId);

      if (activeSessionId === sessionId) {
        setMessages((previous) => [
          ...previous,
          {
            id: `assistant_${Date.now()}`,
            role: "assistant",
            content: result.response,
          },
        ]);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;

      if (activeSessionId === sessionId) {
        setMessages((previous) => [
          ...previous,
          {
            id: `error_${Date.now()}`,
            role: "assistant",
            content:
              detail ||
              "I couldn't process that request. Please check your backend connection and try again.",
            isError: true,
          },
        ]);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleNewChat() {
    const session = createSession();

    setSessions((previous) => [session, ...previous]);
    setActiveSessionId(session.id);
    setMessages([]);
    setError("");
    setSidebarOpen(false);
    inputRef.current?.focus();
  }

  async function handleDeleteSession(sessionId) {
    const confirmed = window.confirm(
      "Delete this conversation and its saved history?"
    );

    if (!confirmed) return;

    try {
      await deleteHistory(sessionId);

      const remaining = sessions.filter(
        (session) => session.id !== sessionId
      );

      if (sessionId === activeSessionId) {
        const next = remaining[0] || createSession();

        if (remaining.length === 0) {
          setSessions([next]);
        } else {
          setSessions(remaining);
        }

        setActiveSessionId(next.id);
        setMessages([]);
      } else {
        setSessions(remaining);
      }
    } catch {
      setError("Unable to delete conversation. Please try again.");
    }
  }

  const isOnline = health?.status === "healthy";

  const activeSession = sessions.find(
    (session) => session.id === activeSessionId
  );

  return (
    <div className="app-shell">

      {/* LEFT SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>

        <div className="brand">
          <div className="brand-icon">
            <Bot size={25} />
          </div>

          <div>
            <h2>SmartTools</h2>
            <span>AI WORKSPACE</span>
          </div>

          <button
            className="icon-button mobile-close"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        <button className="new-chat-button" onClick={handleNewChat}>
          <Plus size={18} />
          <span>New conversation</span>
        </button>

        <div className="sidebar-section">
          <div className="section-heading">
            <History size={15} />
            <span>RECENT CHATS</span>
          </div>

          <div className="session-list">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`session-item ${
                  session.id === activeSessionId ? "active" : ""
                }`}
              >
                <button
                  className="session-select"
                  onClick={() => {
                    setActiveSessionId(session.id);
                    setSidebarOpen(false);
                  }}
                  title={session.title}
                >
                  <MessageSquare size={15} />
                  <span>{session.title}</span>
                </button>

                <button
                  className="session-delete"
                  onClick={() => handleDeleteSession(session.id)}
                  title="Delete conversation"
                  aria-label={`Delete ${session.title}`}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <div className="connection-icon">
              <Server size={18} />
            </div>

            <div className="connection-info">
              <strong>Backend status</strong>
              <span className={isOnline ? "online" : "offline"}>
                <span className="status-dot" />
                {isOnline ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>

          <div className="sidebar-footer">
            <ShieldCheck size={15} />
            <span>Powered by LangChain & MCP</span>
          </div>
        </div>
      </aside>

      {sidebarOpen && (
        <button
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close menu"
        />
      )}

      {/* MAIN CONTENT */}
      <main className="main-content">

        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button mobile-menu"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu size={20} />
            </button>

            <div>
              <h3>AI Assistant</h3>
              <p>Your intelligent multi-tool workspace</p>
            </div>
          </div>

          <div className="topbar-right">
            <span className={`backend-badge ${isOnline ? "online" : ""}`}>
              <span className="status-dot" />
              {isOnline ? "System online" : "System offline"}
            </span>

            <button
              className="icon-button"
              onClick={handleNewChat}
              title="New conversation"
            >
              <Plus size={19} />
            </button>
          </div>
        </header>

        <div className="workspace">

          {/* CHAT AREA */}
          <section className="chat-panel">

            <div className="chat-heading">
              <div>
                <span className="eyebrow">SMARTTOOLS WORKSPACE</span>
                <h1>{activeSession?.title || "New conversation"}</h1>
              </div>

              <div className="tool-count">
                <Wrench size={15} />
                {tools.length} tools
              </div>
            </div>

            <div className="messages-container">

              {loadingHistory ? (
                <div className="loading-state">
                  <LoaderCircle className="spin" size={24} />
                  <span>Loading conversation...</span>
                </div>
              ) : messages.length === 0 ? (
                <div className="welcome-screen">
                  <div className="welcome-icon">
                    <Sparkles size={32} />
                  </div>

                  <span className="eyebrow">YOUR AI WORKSPACE</span>
                  <h2>What can I help you with?</h2>

                  <p>
                    I'm SmartTools AI, powered by LangChain, Groq and
                    Model Context Protocol. Ask me to use my available tools.
                  </p>

                  <div className="suggestion-grid">
                    <button
                      onClick={() =>
                        setInput("Calculate 250 multiplied by 45.")
                      }
                    >
                      <Calculator size={19} />
                      <span>
                        <strong>Calculate</strong>
                        <small>Perform calculations</small>
                      </span>
                    </button>

                    <button
                      onClick={() =>
                        setInput("Show all employees in the database.")
                      }
                    >
                      <Database size={19} />
                      <span>
                        <strong>Query database</strong>
                        <small>Retrieve stored records</small>
                      </span>
                    </button>

                    <button
                      onClick={() =>
                        setInput("What is the current weather in Hyderabad?")
                      }
                    >
                      <CloudSun size={19} />
                      <span>
                        <strong>Check weather</strong>
                        <small>Get live weather data</small>
                      </span>
                    </button>

                    <button
                      onClick={() =>
                        setInput("Convert 100 USD to INR.")
                      }
                    >
                      <ArrowLeftRight size={19} />
                      <span>
                        <strong>Convert currency</strong>
                        <small>Check exchange rates</small>
                      </span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="message-list">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`message-row ${message.role}`}
                    >
                      <div className="message-avatar">
                        {message.role === "user" ? (
                          <span>Y</span>
                        ) : (
                          <Bot size={19} />
                        )}
                      </div>

                      <div className="message-content">
                        <div className="message-author">
                          {message.role === "user"
                            ? "You"
                            : "SmartTools AI"}
                        </div>

                        <div
                          className={`message-bubble ${
                            message.isError ? "error-message" : ""
                          }`}
                        >
                          {message.content}
                        </div>
                      </div>
                    </div>
                  ))}

                  {loading && (
                    <div className="message-row assistant">
                      <div className="message-avatar">
                        <Bot size={19} />
                      </div>

                      <div className="message-content">
                        <div className="message-author">
                          SmartTools AI
                        </div>

                        <div className="thinking-indicator">
                          <LoaderCircle className="spin" size={17} />
                          Thinking and processing your request...
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}

            </div>

            {error && (
              <div className="error-banner">
                <span>{error}</span>
                <button onClick={() => setError("")}>
                  <X size={16} />
                </button>
              </div>
            )}

            <div className="composer-wrapper">
              <form className="composer" onSubmit={handleSend}>
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (
                      event.key === "Enter" &&
                      !event.shiftKey &&
                      !event.nativeEvent.isComposing
                    ) {
                      event.preventDefault();
                      event.currentTarget.form.requestSubmit();
                    }
                  }}
                  placeholder="Ask SmartTools anything..."
                  rows={1}
                  maxLength={10000}
                  disabled={loading || !isOnline}
                />

                <button
                  className="send-button"
                  type="submit"
                  disabled={!input.trim() || loading || !isOnline}
                  aria-label="Send message"
                >
                  {loading ? (
                    <LoaderCircle className="spin" size={19} />
                  ) : (
                    <Send size={19} />
                  )}
                </button>
              </form>

              <p className="composer-note">
                SmartTools AI can make mistakes. Verify important results.
              </p>
            </div>

          </section>

          {/* RIGHT TOOLS PANEL */}
          <aside className="tools-panel">

            <div className="tools-panel-heading">
              <div>
                <span className="eyebrow">AVAILABLE CAPABILITIES</span>
                <h3>Connected Tools</h3>
              </div>

              <div className="tools-total">{tools.length}</div>
            </div>

            <div className="tools-status-card">
              <div className="tools-status-icon">
                <Activity size={19} />
              </div>

              <div>
                <strong>{isOnline ? "MCP Connected" : "MCP Offline"}</strong>
                <span>
                  {isOnline
                    ? `${health?.mcp_tools ?? 0} tools available`
                    : "Waiting for backend"}
                </span>
              </div>

              {isOnline && (
                <CheckCircle2 size={18} className="success-icon" />
              )}
            </div>

            <button
              className="tools-toggle"
              onClick={() => setToolsOpen((value) => !value)}
            >
              <span>
                <Code2 size={16} />
                Registered tools
              </span>

              <ChevronDown
                size={17}
                className={toolsOpen ? "" : "rotated"}
              />
            </button>

            {toolsOpen && (
              <div className="tools-list">
                {tools.length > 0 ? (
                  tools.map((tool) => {
                    const Icon = getToolIcon(tool.name);

                    return (
                      <div className="tool-item" key={tool.name}>
                        <div className="tool-icon">
                          <Icon size={18} />
                        </div>

                        <div className="tool-details">
                          <strong>
                            {tool.name.replaceAll("_", " ")}
                          </strong>
                          <span>
                            {tool.description || "MCP registered tool"}
                          </span>
                        </div>

                        <span className="tool-active-dot" />
                      </div>
                    );
                  })
                ) : (
                  <p className="empty-tools">
                    No tools discovered yet.
                  </p>
                )}
              </div>
            )}

            <div className="architecture-card">
              <div className="architecture-title">
                <Sparkles size={17} />
                <strong>Technology stack</strong>
              </div>

              {["React + Vite", "FastAPI", "LangChain Agent", "Groq LLM", "MCP Server", "SQLite Memory"].map(
                (item) => (
                  <div className="stack-item" key={item}>
                    <span>{item}</span>
                    <CheckCircle2 size={14} />
                  </div>
                )
              )}
            </div>

            <div className="security-note">
              <ShieldCheck size={17} />
              <span>Tool access is managed by your MCP server.</span>
            </div>

          </aside>

        </div>
      </main>
    </div>
  );
}

export default App;
