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
        
        self.tasks_store: Dict[str, Task] = {}
        logger.info("TaskAgent initialized")
    
    # ========================
    # THOUGHT PROCESS (Reasoning)
    # ========================
    
    def _think_about_email(self, email_subject: str, email_body: str) -> str:
        """
        Think about an email - reasoning step.
        
        Args:
            email_subject: Email subject
            email_body: Email body
            
        Returns:
            Thought/reasoning string
        """
        thought = f"""
        REASONING STEP:
        - Email Subject: {email_subject}
        - Email Length: {len(email_body)} characters
        - Analysis: Determining what actionable tasks exist
        """
        logger.info(f"Agent thinking: {thought}")
        return thought
    
    # ========================
    # ACT (Execution)
    # ========================
    
    def process_email(
        self,
        email_subject: str,
        email_body: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an email and extract tasks (ReAct: THOUGHT + ACT).
        
        Args:
            email_subject: Email subject
            email_body: Email body
            sender: Email sender
            
        Returns:
            Dictionary with extracted tasks and workflow info
        """
        try:
            logger.info(f"Agent processing email: {email_subject}")
            
            # THOUGHT: Analyze the email
            thought = self._think_about_email(email_subject, email_body)
            
            # ACT: Extract tasks using LLM
            if not self.llm_service:
                return {
                    "success": False,
                    "error": "LLM service not initialized",
                    "tasks": []
                }
            
            extraction_result = self.llm_service.extract_tasks(
                email_subject=email_subject,
                email_body=email_body,
                sender=sender
            )
            
            # Store extracted tasks
            created_tasks = []
            for task_data in extraction_result.get("tasks", []):
                task_id = f"task_{uuid.uuid4().hex[:8]}"
                task = TaskCreate(**task_data)
                
                # Store task
                full_task = Task(
                    id=task_id,
                    **task.dict(),
                    source_email=email_subject
                )
                self.tasks_store[task_id] = full_task
                created_tasks.append(full_task.dict())
                
                logger.info(f"Created task: {task_id} - {task_data.get('title')}")
            
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
            return {
                "success": False,
                "error": str(e),
                "tasks": []
            }
    
    def reason_and_plan_task(self, task_id: str) -> Dict[str, Any]:
        """
        Use ReAct to reason about and plan task execution.
        
        Args:
            task_id: ID of the task to plan
            
        Returns:
            Dictionary with reasoning and workflow plan
        """
        try:
            task = self.tasks_store.get(task_id)
            if not task:
                return {"success": False, "error": "Task not found"}
            
            logger.info(f"Agent reasoning about task: {task_id}")
            
            # THOUGHT: Consider task requirements
            thought = f"""
            REASONING FOR TASK: {task.title}
            - Description: {task.description}
            - Priority: {task.priority}
            - Analysis: Determining execution workflow
            """
            
            # ACT: Generate reasoning and workflow
            if not self.llm_service:
                return {
                    "success": False,
                    "error": "LLM service not initialized"
                }
            
            reasoning_result = self.llm_service.reason_about_task(
                task_title=task.title,
                task_description=task.description,
                context=f"Priority: {task.priority}, Tags: {', '.join(task.tags)}"
            )
            
            # Create workflow from reasoning
            if not self.workflow_service:
                return {
                    "success": False,
                    "error": "Workflow service not initialized"
                }
            
            workflow = self.workflow_service.create_workflow(task_id, task.title)
            
            # Add steps from reasoning
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
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task by running its workflow.
        
        Args:
            task_id: ID of the task to execute
            
        Returns:
            Execution result
        """
        try:
            task = self.tasks_store.get(task_id)
            if not task:
                return {"success": False, "error": "Task not found"}
            
            logger.info(f"Agent executing task: {task_id}")
            
            if not self.workflow_service:
                return {
                    "success": False,
                    "error": "Workflow service not initialized"
                }
            
            # Find workflow for this task
            workflow = None
            for wf in self.workflow_service.workflows.values():
                if wf.task_id == task_id:
                    workflow = wf
                    break
            
            if not workflow:
                return {"success": False, "error": "No workflow found for task"}
            
            # ACT: Execute workflow
            execution_result = self.workflow_service.execute_workflow(workflow.workflow_id)
            
            # Update task status
            if execution_result.get("success"):
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
            else:
                task.status = TaskStatus.FAILED
            
            if not self.llm_service:
                return {
                    "success": execution_result.get("success"),
                    "task_id": task_id,
                    "workflow_id": workflow.workflow_id,
                    "task_status": task.status.value,
                    "execution_result": execution_result
                }
            
            # Generate summary
            summary_result = self.llm_service.generate_summary(
                task_title=task.title,
                task_description=task.description,
                execution_results=execution_result
            )
            
            return {
                "success": execution_result.get("success"),
                "task_id": task_id,
                "workflow_id": workflow.workflow_id,
                "task_status": task.status.value,
                "execution_result": execution_result,
                "summary": summary_result.get("summary"),
                "key_points": summary_result.get("key_points", []),
                "next_actions": summary_result.get("next_actions", [])
            }
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ========================
    # MEMORY & CONTEXT
    # ========================
    
    def retrieve_similar_tasks(self, query: str, limit: int = 5) -> List[Task]:
        """
        Retrieve similar past tasks for context.
        
        Args:
            query: Search query
            limit: Maximum number of tasks to return
            
        Returns:
            List of similar tasks
        """
        try:
            logger.info(f"Retrieving similar tasks for query: {query}")
            
            # Simple keyword matching (in production, use semantic search with FAISS)
            similar_tasks = []
            for task in self.tasks_store.values():
                if any(keyword.lower() in task.title.lower() or 
                       keyword.lower() in task.description.lower()
                       for keyword in query.split()):
                    similar_tasks.append(task)
            
            return similar_tasks[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving similar tasks: {e}")
            return []
    
    def get_agent_state(self) -> Dict[str, Any]:
        """
        Get current state of the agent.
        
        Returns:
            Dictionary with agent state info
        """
        active_workflows = 0
        if self.workflow_service:
            active_workflows = len([w for w in self.workflow_service.workflows.values() 
                                   if w.state == WorkflowState.RUNNING])
        
        total_workflows = 0
        if self.workflow_service:
            total_workflows = len(self.workflow_service.workflows)
        
        return {
            "tasks_total": len(self.tasks_store),
            "tasks_completed": len([t for t in self.tasks_store.values() 
                                   if t.status == TaskStatus.COMPLETED]),
            "tasks_pending": len([t for t in self.tasks_store.values() 
                                 if t.status == TaskStatus.PENDING]),
            "workflows_active": active_workflows,
            "total_workflows": total_workflows
        }
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task."""
        task = self.tasks_store.get(task_id)
        return task.dict() if task else None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        return [task.dict() for task in self.tasks_store.values()]