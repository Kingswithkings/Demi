from __future__ import annotations
import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PendingAction:
    id: str
    user_id: str
    thread_id: str
    channel: str
    action_type: str
    action_payload: Dict[str, Any]


class AuditStore:
    """
    SQLite implementation (investor-friendly: simple, traceable).
    You can later swap to Postgres without changing agent logic.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _conn(self):
        return sqlite3.connect(self.db_path)

    # ---------- Action Logs ----------
    def log_proposed_action(
        self,
        *,
        user_id: str,
        thread_id: str,
        channel: str,
        action_type: str,
        action_payload: Dict[str, Any],
    ) -> str:
        action_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO action_logs
                (id, created_at, user_id, thread_id, channel, action_type, action_payload,
                 confirmation_status, executed, execution_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action_id,
                    utc_now_iso(),
                    user_id,
                    thread_id,
                    channel,
                    action_type,
                    json.dumps(action_payload, ensure_ascii=False),
                    "awaiting_confirmation",
                    0,
                    None,
                ),
            )
        return action_id

    def mark_confirmed(self, action_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE action_logs SET confirmation_status=? WHERE id=?",
                ("confirmed", action_id),
            )

    def mark_rejected(self, action_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE action_logs SET confirmation_status=? WHERE id=?",
                ("rejected", action_id),
            )

    def mark_executed(self, action_id: str, execution_result: Dict[str, Any]) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE action_logs SET executed=?, execution_result=? WHERE id=?",
                (1, json.dumps(execution_result, ensure_ascii=False), action_id),
            )

    # ---------- Pending Actions ----------
    def create_pending(
        self,
        *,
        user_id: str,
        thread_id: str,
        channel: str,
        action_type: str,
        action_payload: Dict[str, Any],
    ) -> str:
        pending_id = str(uuid.uuid4())
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO pending_actions
                (id, created_at, user_id, thread_id, channel, action_type, action_payload, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pending_id,
                    utc_now_iso(),
                    user_id,
                    thread_id,
                    channel,
                    action_type,
                    json.dumps(action_payload, ensure_ascii=False),
                    "awaiting_confirmation",
                ),
            )
        return pending_id

    def get_pending(self, *, user_id: str, thread_id: str) -> Optional[PendingAction]:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT id, user_id, thread_id, channel, action_type, action_payload
                FROM pending_actions
                WHERE user_id=? AND thread_id=?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, thread_id),
            ).fetchone()

        if not row:
            return None

        return PendingAction(
            id=row[0],
            user_id=row[1],
            thread_id=row[2],
            channel=row[3],
            action_type=row[4],
            action_payload=json.loads(row[5]),
        )

    def clear_pending(self, pending_id: str) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM pending_actions WHERE id=?", (pending_id,))
