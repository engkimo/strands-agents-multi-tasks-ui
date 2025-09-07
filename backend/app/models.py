from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ToolName(str, Enum):
    claude_code = "claude_code"
    codex_cli = "codex_cli"
    gemini_cli = "gemini_cli"
    spec_kit = "spec_kit"


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class RunCreate(BaseModel):
    prompt: str
    tools: List[ToolName] = Field(default_factory=list)
    timeout_seconds: Optional[int] = 120
    metadata: Optional[dict[str, Any]] = None


class NodeResult(BaseModel):
    tool: ToolName
    ok: bool
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: Optional[int] = None
    score: Optional[float] = None


class Run(BaseModel):
    id: str
    status: RunStatus
    prompt: str
    tools: List[ToolName]
    created_at: datetime
    ended_at: Optional[datetime] = None
    results: List[NodeResult] = Field(default_factory=list)
    best_tool: Optional[ToolName] = None
    best_score: Optional[float] = None
