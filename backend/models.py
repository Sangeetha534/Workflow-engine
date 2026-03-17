from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

    steps = relationship("Step", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")

class Step(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    name = Column(String)
    step_type = Column(String) # 'start', 'action', 'condition', 'end'

    workflow = relationship("Workflow", back_populates="steps")
    # A step can have multiple rules
    rules = relationship("Rule", primaryjoin="Step.id==Rule.step_id", back_populates="step", cascade="all, delete-orphan")

class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    step_id = Column(Integer, ForeignKey("steps.id"))
    condition = Column(String) # e.g., "amount > 100", or "DEFAULT"
    priority = Column(Integer, default=0)
    next_step_id = Column(Integer, ForeignKey("steps.id"), nullable=True)

    step = relationship("Step", foreign_keys=[step_id], back_populates="rules")
    next_step = relationship("Step", foreign_keys=[next_step_id])

class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"))
    status = Column(String) # e.g., "running", "completed", "error"

    workflow = relationship("Workflow", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"))
    step_name = Column(String)
    evaluated_rules = Column(JSON) # e.g., [{"condition": "amount > 100", "result": True}]
    next_step = Column(String, nullable=True)
    status = Column(String)

    execution = relationship("Execution", back_populates="logs")
