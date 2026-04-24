"""
Data models for Task management.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Enum for task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(str, Enum):
    """Enum for task priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskBase(BaseModel):
    """Base model for Task."""
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    assigned_to: Optional[str] = Field(None, description="Person assigned to task")
    tags: List[str] = Field(default_factory=list, description="Task tags")


class TaskCreate(TaskBase):
    """Model for creating a new task."""
    source_email: Optional[str] = Field(None, description="Source email ID")
    extracted_from: Optional[str] = Field(None, description="Text/email content task was extracted from")


class TaskUpdate(BaseModel):
    """Model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None


class Task(TaskBase):
    """Task model returned from API."""
    id: str = Field(..., description="Unique task ID")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    source_email: Optional[str] = Field(None, description="Source email ID")
    extracted_from: Optional[str] = Field(None, description="Text/email content task was extracted from")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "task_001",
                "title": "Review project proposal",
                "description": "Review the Q2 project proposal from the marketing team",
                "priority": "high",
                "status": "pending",
                "due_date": "2026-05-01T00:00:00",
                "assigned_to": "john@example.com",
                "tags": ["project", "review"],
                "source_email": "email_123",
                "created_at": "2026-04-24T10:00:00",
                "updated_at": "2026-04-24T10:00:00",
                "completed_at": None
            }
        }


class TaskListResponse(BaseModel):
    """Response model for task list."""
    total: int = Field(..., description="Total number of tasks")
    tasks: List[Task] = Field(..., description="List of tasks")


class TaskExtractionRequest(BaseModel):
    """Request model for task extraction from email."""
    email_subject: str = Field(..., description="Email subject")
    email_body: str = Field(..., description="Email body content")
    sender: Optional[str] = Field(None, description="Email sender")


class ExtractedTasks(BaseModel):
    """Model for extracted tasks."""
    tasks: List[TaskCreate] = Field(..., description="List of extracted tasks")
    summary: str = Field(..., description="Summary of extraction")
    confidence: float = Field(..., ge=0, le=1, description="Extraction confidence score")