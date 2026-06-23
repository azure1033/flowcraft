"""SQLAlchemy ORM models for FlowCraft — design D4.

Supports both SQLite (local dev) and PostgreSQL (production).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    JSON,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class WorkflowDefinition(Base):
    __tablename__ = "workflow_definitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    definition = Column(JSON, nullable=False)
    version = Column(Integer, default=1)
    source = Column(String(50), default="local")  # [EXTENSIBLE] marketplace
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tasks = relationship("TaskInstance", back_populates="workflow")


class TaskInstance(Base):
    __tablename__ = "task_instances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, ForeignKey("workflow_definitions.id"), nullable=False)
    status = Column(
        String(20), default="pending"
    )  # pending/running/waiting_human/completed/failed
    trigger_type = Column(
        String(20), default="manual"
    )  # [EXTENSIBLE] scheduled/webhook
    task_input = Column(Text, default="")
    created_by = Column(String(100), default="api")
    current_state_snapshot = Column(JSON)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    workflow = relationship("WorkflowDefinition", back_populates="tasks")
    node_executions = relationship("NodeExecution", back_populates="task")
    human_decisions = relationship("HumanDecision", back_populates="task")


class NodeExecution(Base):
    __tablename__ = "node_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("task_instances.id"), nullable=False)
    node_id = Column(String, nullable=False)
    node_type = Column(String, nullable=False)
    status = Column(String(20), default="running")  # running/success/error/interrupted
    input_snapshot = Column(JSON)
    output_snapshot = Column(JSON)
    started_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)

    task = relationship("TaskInstance", back_populates="node_executions")


class HumanDecision(Base):
    __tablename__ = "human_decisions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("task_instances.id"), nullable=False)
    node_id = Column(String, nullable=False)
    decision = Column(String(20), nullable=False)  # approved/rejected
    feedback = Column(Text, default="")
    decided_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    decided_by = Column(String(100), default="api")

    task = relationship("TaskInstance", back_populates="human_decisions")
