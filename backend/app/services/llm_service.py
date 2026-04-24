"""
LLM Service for AI interactions using LangChain.
"""
import json
import logging
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from backend.config import settings
from backend.app.utils.prompts import (
    TASK_EXTRACTION_PROMPT,
    TASK_REASONING_PROMPT,
    TASK_EXECUTION_PROMPT,
    SUMMARY_GENERATION_PROMPT,
    MEMORY_RETRIEVAL_PROMPT
)

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions."""
    
    def __init__(self):
        """Initialize LLM service with OpenAI configuration."""
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model_name=settings.model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
        logger.info(f"LLMService initialized with model: {settings.model_name}")
    
    def extract_tasks(
        self,
        email_subject: str,
        email_body: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract tasks from an email using LLM.
        
        Args:
            email_subject: Subject of the email
            email_body: Body/content of the email
            sender: Email sender
            
        Returns:
            Dictionary containing extracted tasks, summary, and confidence
        """
        try:
            # Create prompt template
            prompt = PromptTemplate(
                input_variables=["email_subject", "email_body", "sender"],
                template=TASK_EXTRACTION_PROMPT
            )
            
            # Create chain
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Run chain
            response = chain.run(
                email_subject=email_subject,
                email_body=email_body,
                sender=sender or "Unknown"
            )
            
            # Parse JSON response
            extracted_data = json.loads(response)
            logger.info(f"Successfully extracted {len(extracted_data.get('tasks', []))} tasks")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {
                "tasks": [],
                "summary": "Failed to extract tasks",
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Error in task extraction: {e}")
            raise
    
    def reason_about_task(
        self,
        task_title: str,
        task_description: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to reason about task execution steps.
        
        Args:
            task_title: Title of the task
            task_description: Description of the task
            context: Additional context
            
        Returns:
            Dictionary containing workflow steps and reasoning
        """
        try:
            prompt = PromptTemplate(
                input_variables=["task_title", "task_description", "context"],
                template=TASK_REASONING_PROMPT
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            response = chain.run(
                task_title=task_title,
                task_description=task_description,
                context=context or "No additional context"
            )
            
            reasoning_data = json.loads(response)
            logger.info(f"Reasoning completed for task: {task_title}")
            
            return reasoning_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse reasoning response: {e}")
            return {
                "workflow_steps": [],
                "required_information": [],
                "reasoning": "Failed to generate reasoning"
            }
        except Exception as e:
            logger.error(f"Error in task reasoning: {e}")
            raise
    
    def generate_summary(
        self,
        task_title: str,
        task_description: str,
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a summary of task execution.
        
        Args:
            task_title: Title of the task
            task_description: Description of the task
            execution_results: Results from execution
            
        Returns:
            Dictionary containing summary and key points
        """
        try:
            prompt = PromptTemplate(
                input_variables=["task_title", "task_description", "execution_results"],
                template=SUMMARY_GENERATION_PROMPT
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            response = chain.run(
                task_title=task_title,
                task_description=task_description,
                execution_results=json.dumps(execution_results)
            )
            
            summary_data = json.loads(response)
            logger.info(f"Summary generated for task: {task_title}")
            
            return summary_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse summary response: {e}")
            return {
                "summary": "Failed to generate summary",
                "key_points": [],
                "status": "unknown"
            }
        except Exception as e:
            logger.error(f"Error in summary generation: {e}")
            raise
    
    def retrieve_memory_context(
        self,
        query: str,
        similar_tasks: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Retrieve memory context for a task.
        
        Args:
            query: Query about tasks
            similar_tasks: Similar past tasks
            
        Returns:
            Dictionary containing retrieved context and suggestions
        """
        try:
            prompt = PromptTemplate(
                input_variables=["query", "similar_tasks"],
                template=MEMORY_RETRIEVAL_PROMPT
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            response = chain.run(
                query=query,
                similar_tasks=json.dumps(similar_tasks) if similar_tasks else "[]"
            )
            
            memory_data = json.loads(response)
            logger.info(f"Memory context retrieved for query: {query}")
            
            return memory_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse memory response: {e}")
            return {
                "similar_approaches": [],
                "pitfalls_to_avoid": [],
                "best_practices": [],
                "confidence": 0.0
            }
        except Exception as e:
            logger.error(f"Error in memory retrieval: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the current LLM model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "model": settings.model_name,
            "temperature": str(settings.temperature),
            "max_tokens": str(settings.max_tokens),
            "provider": "OpenAI"
        }