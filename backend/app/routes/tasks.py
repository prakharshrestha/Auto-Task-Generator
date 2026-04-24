"""
API routes for task management.
"""
import logging
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional

from app.models.task import (
    Task, TaskCreate, TaskUpdate, TaskListResponse,
    TaskExtractionRequest, ExtractedTasks
)
from app.agents.task_agent import TaskAgent

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Initialize agent (in production, use dependency injection)
agent = TaskAgent()


@router.post("/extract", response_model=ExtractedTasks)
async def extract_tasks_from_email(request: TaskExtractionRequest):
    """
    Extract tasks from an email.
    
    Args:
        request: Email content to extract tasks from
        
    Returns:
        Extracted tasks
    """
    try:
        result = agent.process_email(
            email_subject=request.email_subject,
            email_body=request.email_body,
            sender=request.sender
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Convert to ExtractedTasks format
        return ExtractedTasks(
            tasks=[TaskCreate(**task) for task in result.get("tasks", [])],
            summary=result.get("summary", ""),
            confidence=result.get("confidence", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error extracting tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/reason", response_model=dict)
async def reason_about_task(task_id: str):
    """
    Reason and plan a task using AI.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Reasoning and workflow plan
    """
    try:
        result = agent.reason_and_plan_task(task_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error reasoning about task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/execute", response_model=dict)
async def execute_task(task_id: str):
    """
    Execute a task.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Execution result
    """
    try:
        result = agent.execute_task(task_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    skip: int = 0,
    limit: int = 10,
    status: Optional[str] = None
):
    """
    List all tasks with optional filtering.
    
    Args:
        skip: Number of tasks to skip
        limit: Maximum number of tasks to return
        status: Filter by task status
        
    Returns:
        List of tasks
    """
    try:
        all_tasks = agent.get_all_tasks()
        
        # Filter by status if provided
        if status:
            all_tasks = [t for t in all_tasks if t.get("status") == status]
        
        # Apply pagination
        paginated_tasks = all_tasks[skip:skip + limit]
        
        return TaskListResponse(
            total=len(all_tasks),
            tasks=paginated_tasks
        )
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """
    Get a specific task by ID.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Task details
    """
    try:
        task = agent.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}", response_model=Task)
async def update_task(task_id: str, update_data: TaskUpdate):
    """
    Update a task.
    
    Args:
        task_id: ID of the task
        update_data: Fields to update
        
    Returns:
        Updated task
    """
    try:
        task = agent.tasks_store.get(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update task fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(task, field, value)
        
        from datetime import datetime
        task.updated_at = datetime.utcnow()
        
        return task.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a task.
    
    Args:
        task_id: ID of the task
        
    Returns:
        Success message
    """
    try:
        if task_id not in agent.tasks_store:
            raise HTTPException(status_code=404, detail="Task not found")
        
        del agent.tasks_store[task_id]
        
        return {"message": f"Task {task_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/similar")
async def search_similar_tasks(query: str, limit: int = 5):
    """
    Search for similar tasks.
    
    Args:
        query: Search query
        limit: Maximum results
        
    Returns:
        Similar tasks
    """
    try:
        similar_tasks = agent.retrieve_similar_tasks(query, limit)
        
        return {
            "query": query,
            "count": len(similar_tasks),
            "tasks": [task.dict() for task in similar_tasks]
        }
        
    except Exception as e:
        logger.error(f"Error searching tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/agent")
async def get_agent_stats():
    """
    Get agent statistics.
    
    Returns:
        Agent statistics
    """
    try:
        stats = agent.get_agent_state()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))