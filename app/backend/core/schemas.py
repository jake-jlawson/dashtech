from pydantic import BaseModel, Field
from typing import Any, Dict, Union
import uuid, datetime

class InboundMessage(BaseModel):
    id: str
    type: str
    v: int = 1
    issue_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)

    # Optional envelope fields we want for routing/idempotency
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())
    source: str = "test"  # "ws" | "cli" | "test" | "system"

    @classmethod
    def ensure_envelope(cls, msg: Union["InboundMessage", Dict[str, Any]]) -> "InboundMessage":
        """
        Accepts either:
          - InboundMessage (returns as-is)
          - legacy dicts -> wraps extras into payload and fills defaults
        """
        if isinstance(msg, InboundMessage):
            return msg

        if not isinstance(msg, dict):
            raise TypeError("Event must be a dict or InboundMessage")

        # If no payload key, wrap all non-envelope keys into payload
        base_keys = {"type", "issue_id", "v", "payload", "meta", "id", "ts", "source"}
        if "payload" not in msg:
            extras = {k: v for k, v in msg.items() if k not in base_keys}
            msg = {
                "id": msg.get("id", str(uuid.uuid4())),
                "type": msg.get("type"),
                "issue_id": msg.get("issue_id"),
                "v": msg.get("v", 1),
                "payload": msg.get("payload", extras),
                "meta": msg.get("meta", {}),
                "id": msg.get("id", str(uuid.uuid4())),
                "ts": msg.get("ts", datetime.datetime.utcnow().isoformat()),
                "source": msg.get("source", "test"),
            }

        # Let Pydantic validate/typeset and fill defaults
        return cls.model_validate(msg)


event_types = [
    "issue.created",
    "issue.attached",
    "issue.create_rejected",
    "issue.attach_rejected",
    "issue.closed",
    "issue.updated",
    "issue.updated_rejected",
    "issue.updated_rejected",
]