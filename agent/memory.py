
import json
import sqlite3

from contextlib import closing
from pathlib import Path

from langchain_core.messages import (
    messages_to_dict,
    messages_from_dict,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

MEMORY_DB = (
    PROJECT_ROOT
    / "database"
    / "conversation_memory.db"
)


class ConversationMemory:
    """Persistent SQLite-based conversation memory."""

    def __init__(self, db_path: Path = MEMORY_DB):

        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize_database()

    def initialize_database(self):
        """Create the conversation storage table."""

        with closing(
            sqlite3.connect(self.db_path)
        ) as connection:

            with connection:

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        session_id TEXT PRIMARY KEY,
                        messages_json TEXT NOT NULL,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

    def load(self, session_id: str = "default"):
        """Load previous messages for a conversation."""

        with closing(
            sqlite3.connect(self.db_path)
        ) as connection:

            cursor = connection.execute(
                """
                SELECT messages_json
                FROM conversations
                WHERE session_id = ?
                """,
                (session_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return []

        try:

            serialized_messages = json.loads(row[0])

            return messages_from_dict(
                serialized_messages
            )

        except (json.JSONDecodeError, TypeError, ValueError):

            raise RuntimeError(
                "Unable to restore conversation history. "
                "The stored conversation data may be corrupted."
            )

    def save(
        self,
        messages,
        session_id: str = "default",
    ):
        """Save the complete conversation history."""

        serialized_messages = messages_to_dict(
            messages
        )

        messages_json = json.dumps(
            serialized_messages
        )

        with closing(
            sqlite3.connect(self.db_path)
        ) as connection:

            with connection:

                connection.execute(
                    """
                    INSERT INTO conversations (
                        session_id,
                        messages_json,
                        updated_at
                    )
                    VALUES (?, ?, CURRENT_TIMESTAMP)

                    ON CONFLICT(session_id)
                    DO UPDATE SET
                        messages_json = excluded.messages_json,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (session_id, messages_json),
                )

    def clear(self, session_id: str = "default"):
        """Delete the stored conversation."""

        with closing(
            sqlite3.connect(self.db_path)
        ) as connection:

            with connection:

                connection.execute(
                    """
                    DELETE FROM conversations
                    WHERE session_id = ?
                    """,
                    (session_id,),
                )

    def count(self, session_id: str = "default") -> int:
        """Return the number of stored messages."""

        return len(
            self.load(session_id)
        )
