from typing import Any, Dict, List, Set, Optional, Tuple
from enum import Enum
import uuid
import datetime
import asyncio
from fastapi import WebSocket


class IssueStatus(Enum):
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"


class IssueContext:
    def __init__(self):
        self.id: str = str(uuid.uuid4())
        self.created_at: str = datetime.datetime.utcnow().isoformat()
        self.status: IssueStatus = IssueStatus.ACTIVE
        self._q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

        # Manage connection
        self.connection: Optional[WebSocket] = None
        self._send_lock: asyncio.Lock = asyncio.Lock()

    def ingest(self, msg: Dict[str, Any]) -> None:
        """
        Ingest a message from the client.
        """
        self._queue.put_nowait(msg)



class IssueManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self.current: Optional[IssueContext] = None
        print("IssueManager initialized", flush=True)

    async def get_current(self) -> Optional[IssueContext]:
        """
        Get the current issue context.
        """
        return self.current

    async def create_issue(self) -> IssueContext:
        """
        Create a new issue context if there is not one already, or return the existing one.
        Returns the issue context and a boolean indicating if a new one was created.
        """
        async with self._lock:
            if self.current is None:
                self.current = IssueContext()
                print("Issue created", flush=True)
                return self.current
            else:
                print("Issue already exists", flush=True)
                return self.current

    async def set_connection(self, issue: IssueContext, connection: WebSocket):
        """
        Set the connection for the issue.
        """
        old = issue.connection
        if old is not None and old is not ws:
            try:
                await old.close(code=1000)
            except Exception:
                pass
        issue.connection = connection

    async def clear_connection(self, issue: IssueContext):
        """
        Clear the connection for the issue.
        """
        issue.connection = None






