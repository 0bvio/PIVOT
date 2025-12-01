from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

_lock = threading.Lock()
_sessions: Dict[str, "Session"] = {}


@dataclass
class Session:
    id: str
    project: str
    created_at: float
    ended_at: Optional[float] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def append(self, role: str, content: str, metadata: Optional[dict] = None):
        self.messages.append({"role": role, "content": content, "ts": time.time(), "metadata": metadata or {}})


def start_session(project: str = "default") -> Session:
    with _lock:
        sid = str(uuid.uuid4())
        s = Session(id=sid, project=project, created_at=time.time())
        _sessions[sid] = s
        return s


def end_session(session_id: str) -> bool:
    with _lock:
        s = _sessions.get(session_id)
        if not s:
            return False
        s.ended_at = time.time()
        return True


def get_session(session_id: str) -> Optional[Session]:
    return _sessions.get(session_id)


def list_sessions() -> List[Session]:
    return list(_sessions.values())


def append_message(session_id: str, role: str, content: str, metadata: Optional[dict] = None) -> bool:
    s = _sessions.get(session_id)
    if not s:
        return False
    s.append(role, content, metadata)
    return True

