"""
Task Agent for autonomous task execution using ReAct pattern.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from app.services.llm_service import LLMService
from app.services.email_service import EmailService
from app.services.workflow_service import WorkflowService, WorkflowState
from app.models.task import Task, TaskStatus, TaskCreate

from app.database import SessionLocal
from app.models.db_models import DBTask

logger = logging.getLogger(__name__)


class TaskAgent:
    """
    Autonomous agent for task extraction, reasoning, and execution.
    Uses ReAct (Reasoning + Acting) pattern.
    """
    
    def __init__(self):
        """Initialize the task agent."""
        try:
            self.llm_service = LLMService()
        except Exception as e:
            logger.error(f"Failed to initialize LLMService: {e}")
            self.llm_service = None
        
        try:
            self.email_service = EmailService()
        except Exception as e:
            logger.error(f"Failed to initialize EmailService: {e}")
            self.email_service = None
        
        try:
            self.workflow_service = WorkflowService()
        except Exception as e:
            logger.error(f"Failed to initialize WorkflowService: {e}")
            self.workflow_service = None
        
        logger.info("TaskAgent initialized")
    
    def _think_about_email(self, email_subject: str, email_body: str) -> str:
        thought = f"""
        REASONING STEP:
        - Email Subject: {email_subject}
        - Email Length: {len(email_body)} characters
        - Analysis: Determining what actionable tasks exist
        """
        logger.info(f"Agent thinking: {thought}")
        return thought
    
    def process_email(
        self,
        email_subject: str,
        email_body: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Agent processing email: {email_subject}")
            thought = self._think_about_email(email_subject, email_body)
            
            if not self.llm_service:
                return {"success": False, "error": "LLM service not initialized", "tasks": []}
            
            extraction_result = self.llm_service.extract_tasks(
                email_subject=email_subject,
                email_body=email_body,
                sender=sender
            )
            
            created_tasks = []
            db = SessionLocal()
            try:
                for task_data in extraction_result.get("tasks", []):
                    task_id = f"task_{uuid.uuid4().hex[:8]}"
                    
                    # Use Pydantic to validate and normalize (e.g. due_date)
                    try:
                        validated_task = TaskCreate(**task_data)
                    except Exception as e:
                        logger.error(f"Validation error for task {task_data}: {e}")
                        continue
                        
                    db_task = DBTask(
                        id=task_id,
                        title=validated_task.title,
                        description=validated_task.description,
                        priority=validated_task.priority.value,
                        due_date=validated_task.due_date,
                        assigned_to=validated_task.assigned_to,
                        tags=validated_task.tags,
                        source_email=email_subject,
                        extracted_from=email_body[:500] if email_body else None
                    )
                    db.add(db_task)
                    
                    # Return dict format expected by the router
                    task_dict = {
                        "id": task_id,
                        "title": db_task.title,
                        "description": db_task.description,
                        "priority": db_task.priority,
                        "status": db_task.status,
                        "tags": db_task.tags,
                        "source_email": db_task.source_email,
                        "created_at": datetime.utcnow()
                    }
                    created_tasks.append(task_dict)
                    logger.info(f"Created task: {task_id} - {db_task.title}")
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Database error during extraction: {e}")
            finally:
                db.close()
            
            return {
                "success": True,
                "thought_process": thought,
                "tasks_extracted": len(created_tasks),
                "tasks": created_tasks,
                "summary": extraction_result.get("summary"),
                "confidence": extraction_result.get("confidence")
            }
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return {"success": False, "error": str(e), "tasks": []}
    
    def reason_and_plan_task(self, task_id: str) -> Dict[str, Any]:
        try:
            db = SessionLocal()
            try:
                db_task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not db_task:
                    return {"success": False, "error": "Task not found"}
                
                title = db_task.title
                description = db_task.description
                priority = db_task.priority
                tags = db_task.tags
            finally:
                db.close()
            
            logger.info(f"Agent reasoning about task: {task_id}")
            
            thought = f"""
            REASONING FOR TASK: {title}
            - Description: {description}
            - Priority: {priority}
            - Analysis: Determining execution workflow
            """
            
            if not self.llm_service:
                return {"success": False, "error": "LLM service not initialized"}
            
            reasoning_result = self.llm_service.reason_about_task(
                task_title=title,
                task_description=description,
                context=f"Priority: {priority}, Tags: {', '.join(tags)}"
            )
            
            if not self.workflow_service:
                return {"success": False, "error": "Workflow service not initialized"}
            
            workflow = self.workflow_service.create_workflow(task_id, title)
            
            for idx, step_data in enumerate(reasoning_result.get("workflow_steps", []), 1):
                step_id = f"step_{idx}"
                self.workflow_service.add_workflow_step(
                    workflow_id=workflow.workflow_id,
                    step_id=step_id,
                    action=step_data.get("action", ""),
                    tool=step_data.get("tool_required", ""),
                    parameters=step_data.get("parameters", {}),
                    description=step_data.get("expected_output", "")
                )
            
            return {
                "success": True,
                "task_id": task_id,
                "thought_process": thought,
                "workflow_id": workflow.workflow_id,
                "reasoning": reasoning_result.get("reasoning"),
                "workflow_steps": len(workflow.steps),
                "required_information": reasoning_result.get("required_information", []),
                "estimated_time": reasoning_result.get("estimated_time"),
                "risks": reasoning_result.get("risks", [])
            }
            
        except Exception as e:
            logger.error(f"Error reasoning about task: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        try:
            db = SessionLocal()
            try:
                db_task = db.query(DBTask).filter(DBTask.id == task_id).first()
                if not db_task:
                    return {"success": False, "error": "Task not found"}
                
                title = db_task.title
                description = db_task.description
                
                logger.info(f"Agent executing task: {task_id}")
                
                if not self.workflow_service:
                    return {"success": False, "error": "Workflow service not initialized"}
                
                workflow = None
                for wf in self.workflow_service.workflows.values():
                    if wf.task_id == task_id:
                        workflow = wf
                        break
                
                if not workflow:
                    return {"success": False, "error": "No workflow found for task"}
                
                execution_result = self.workflow_service.execute_workflow(workflow.workflow_id)
                
                if execution_result.get("success"):
                    db_task.status = TaskStatus.COMPLETED.value
                    db_task.completed_at = datetime.utcnow()
                else:
                    db_task.status = TaskStatus.FAILED.value
                db.commit()
                
                status_value = db_task.status
            finally:
                db.close()
            
            if not self.llm_service:
                return {
                    "success": execution_result.get("success"),
                    "task_id": task_id,
                    "workflow_id": workflow.workflow_id,
                    "task_status": status_value,
                    "execution_result": execution_result
                }
            
            summary_result = self.llm_service.generate_summary(
                task_title=title,
                task_description=description,
                execution_results=execution_result
            )
            
            return {
                "success": execution_result.get("success"),
                "task_id": task_id,
                "workflow_id": workflow.workflow_id,
                "task_status": status_value,
                "execution_result": execution_result,
                "summary": summary_result.get("summary"),
                "key_points": summary_result.get("key_points", []),
                "next_actions": summary_result.get("next_actions", [])
            }
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {"success": False, "error": str(e)}
    
    def retrieve_similar_tasks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            # Simple keyword matching in DB for MVP
            query_terms = query.lower().split()
            all_tasks = db.query(DBTask).all()
            
            similar_tasks = []
            for task in all_tasks:
                if any(keyword in task.title.lower() or 
                       keyword in task.description.lower() 
                       for keyword in query_terms):
                    similar_tasks.append(self._db_task_to_dict(task))
            
            return similar_tasks[:limit]
        except Exception as e:
            logger.error(f"Error retrieving similar tasks: {e}")
            return []
        finally:
            db.close()
    
    def get_agent_state(self) -> Dict[str, Any]:
        active_workflows = 0
        total_workflows = 0
        if self.workflow_service:
            active_workflows = len([w for w in self.workflow_service.workflows.values() 
                                   if w.state == WorkflowState.RUNNING])
            total_workflows = len(self.workflow_service.workflows)
        
        db = SessionLocal()
        try:
            tasks_total = db.query(DBTask).count()
            tasks_completed = db.query(DBTask).filter(DBTask.status == TaskStatus.COMPLETED.value).count()
            tasks_pending = db.query(DBTask).filter(DBTask.status == TaskStatus.PENDING.value).count()
        except Exception as e:
            logger.error(f"Error getting agent state from DB: {e}")
            tasks_total = tasks_completed = tasks_pending = 0
        finally:
            db.close()
            
        return {
            "tasks_total": tasks_total,
            "tasks_completed": tasks_completed,
            "tasks_pending": tasks_pending,
            "workflows_active": active_workflows,
            "total_workflows": total_workflows
        }
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            return self._db_task_to_dict(task) if task else None
        finally:
            db.close()
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            tasks = db.query(DBTask).order_by(DBTask.created_at.desc()).all()
            return [self._db_task_to_dict(task) for task in tasks]
        finally:
            db.close()

    def create_task(self, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            db_task = DBTask(
                id=task_id,
                title=task_data.get("title", "Untitled"),
                description=task_data.get("description", ""),
                priority=task_data.get("priority", "medium"),
                due_date=task_data.get("due_date"),
                assigned_to=task_data.get("assigned_to"),
                tags=task_data.get("tags", []),
                source_email=task_data.get("source_email", "manual"),
                status=task_data.get("status", "pending")
            )
            db.add(db_task)
            db.commit()
            db.refresh(db_task)
            return self._db_task_to_dict(db_task)
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating manual task: {e}")
            raise
        finally:
            db.close()

    def update_task(self, task_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if not task:
                return None
            
            for key, value in update_data.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            db.commit()
            db.refresh(task)
            return self._db_task_to_dict(task)
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating task: {e}")
            raise
        finally:
            db.close()

    def delete_task(self, task_id: str) -> bool:
        db = SessionLocal()
        try:
            task = db.query(DBTask).filter(DBTask.id == task_id).first()
            if not task:
                return False
            db.delete(task)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting task: {e}")
            return False
        finally:
            db.close()

    def _db_task_to_dict(self, db_task: DBTask) -> Dict[str, Any]:
        """Convert a DBTask to a dictionary matching the Task Pydantic model."""
        return {
            "id": db_task.id,
            "title": db_task.title,
            "description": db_task.description,
            "priority": db_task.priority,
            "status": db_task.status,
            "due_date": db_task.due_date,
            "assigned_to": db_task.assigned_to,
            "tags": db_task.tags,
            "source_email": db_task.source_email,
            "extracted_from": db_task.extracted_from,
            "created_at": db_task.created_at,
            "updated_at": db_task.updated_at,
            "completed_at": db_task.completed_at
        }