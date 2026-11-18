
import json
import logging
import threading
import time

from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler


# =========================================================
# AUDIT LOG CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIRECTORY = PROJECT_ROOT / "logs"
AUDIT_FILE = AUDIT_DIRECTORY / "tool_audit.jsonl"

AUDIT_DIRECTORY.mkdir(parents=True, exist_ok=True)

audit_logger = logging.getLogger("smarttools.tool_audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False

# Avoid adding duplicate handlers during module reloads.
if not audit_logger.handlers:
    file_handler = RotatingFileHandler(
        AUDIT_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    audit_logger.addHandler(file_handler)


# =========================================================
# MCP TOOL AUDIT CALLBACK
# =========================================================

class ToolAuditCallback(AsyncCallbackHandler):
    """
    Records actual LangChain tool execution events.

    Sensitive tool arguments and outputs are deliberately
    excluded from the audit log.
    """

    def __init__(self, session_id: str):
        super().__init__()

        self.session_id = session_id
        self.started_tools: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def _write_event(
        self,
        event: str,
        tool_name: str,
        run_id: Any,
        status: str,
        duration_ms: float | None = None,
        error_type: str | None = None,
    ) -> None:
        """Write a privacy-conscious JSON audit record."""

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(
                timespec="milliseconds"
            ),
            "session_id": self.session_id,
            "event": event,
            "tool_name": tool_name,
            "run_id": str(run_id),
            "status": status,
        }

        if duration_ms is not None:
            record["duration_ms"] = round(duration_ms, 2)

        if error_type is not None:
            record["error_type"] = error_type

        try:
            with self.lock:
                audit_logger.info(
                    json.dumps(record, ensure_ascii=False)
                )
        except Exception:
            # Audit failures must not interrupt agent execution.
            logging.getLogger("smarttools").exception(
                "Unable to write MCP tool audit event."
            )

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: Any,
        parent_run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Record when a tool actually starts executing."""

        tool_name = serialized.get("name", "unknown_tool")

        with self.lock:
            self.started_tools[str(run_id)] = {
                "tool_name": tool_name,
                "started_at": time.monotonic(),
            }

        self._write_event(
            event="tool_started",
            tool_name=tool_name,
            run_id=run_id,
            status="running",
        )

    async def on_tool_end(
        self,
        output: Any,
        *,
        run_id: Any,
        parent_run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Record successful tool execution."""

        with self.lock:
            tool_data = self.started_tools.pop(
                str(run_id),
                None,
            )

        if tool_data is None:
            tool_name = "unknown_tool"
            duration_ms = None
        else:
            tool_name = tool_data["tool_name"]
            duration_ms = (
                time.monotonic() - tool_data["started_at"]
            ) * 1000

        self._write_event(
            event="tool_completed",
            tool_name=tool_name,
            run_id=run_id,
            status="success",
            duration_ms=duration_ms,
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        parent_run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Record failed tool execution without logging its message."""

        with self.lock:
            tool_data = self.started_tools.pop(
                str(run_id),
                None,
            )

        if tool_data is None:
            tool_name = "unknown_tool"
            duration_ms = None
        else:
            tool_name = tool_data["tool_name"]
            duration_ms = (
                time.monotonic() - tool_data["started_at"]
            ) * 1000

        self._write_event(
            event="tool_failed",
            tool_name=tool_name,
            run_id=run_id,
            status="failed",
            duration_ms=duration_ms,
            error_type=type(error).__name__,
        )
