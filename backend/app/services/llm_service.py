"""
LLM Service for AI interactions using Ollama (local).
"""
import json
import re
import logging
from typing import Optional, Dict, Any
import requests
from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions using Ollama."""

    def __init__(self):
        """Initialize LLM service with Ollama configuration."""
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        logger.info(f"LLMService initialized with Ollama model: {self.model}")

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat request to Ollama and return the response text."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": self.temperature,
                "num_predict": 800
            }
        }

        response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown code blocks or clean up the string."""
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx+1]
        
        return text

    def extract_tasks(
        self,
        email_subject: str,
        email_body: str,
        sender: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract tasks from an email using Ollama."""
        try:
            prompt = f"""
You are an expert task extraction AI. Your job is to read an email and extract actionable tasks from it.

EMAIL SUBJECT: {email_subject}
EMAIL BODY:
{email_body}
SENDER: {sender or "Unknown"}

Please analyze this email and extract all actionable tasks. For each task, provide:
1. Title: A concise task name
2. Description: Detailed description of what needs to be done
3. Priority: low, medium, high, or urgent (based on email urgency indicators)
4. Due Date: If mentioned, in ISO format (YYYY-MM-DD). If not mentioned, use "not_specified"
5. Assigned To: Who should do this task (if mentioned)
6. Tags: Relevant tags to categorize the task

Return ONLY valid JSON with this structure:
{{
  "tasks": [
    {{
      "title": "task title",
      "description": "task description",
      "priority": "high",
      "due_date": "2026-05-01",
      "assigned_to": "person@example.com",
      "tags": ["tag1", "tag2"]
    }}
  ],
  "summary": "Brief summary of what was extracted",
  "confidence": 0.95
}}
            """

            response_text = self._chat(
                system_prompt="You are a helpful task extraction assistant. Return ONLY valid JSON, without any markdown formatting or explanations.",
                user_prompt=prompt
            )

            clean_json = self._extract_json(response_text)
            extracted_data = json.loads(clean_json)
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
        """Use LLM to reason about task execution steps."""
        try:
            prompt = f"""
You are an intelligent task reasoning and planning agent. Given a task, you need to decide:
1. What workflow steps are needed to complete this task
2. What tools/APIs are needed
3. What information is required
4. Priority level and urgency

TASK: {task_title}
TASK DESCRIPTION: {task_description}
CURRENT CONTEXT: {context or "No additional context"}

Return ONLY valid JSON:
{{
  "workflow_steps": [
    {{
      "step_number": 1,
      "action": "description of action",
      "tool_required": "gmail/slack/notion/custom",
      "parameters": {{}},
      "expected_output": "what this step should produce"
    }}
  ],
  "required_information": ["info1", "info2"],
  "estimated_time": "5 minutes",
  "risks": ["risk1", "risk2"],
  "reasoning": "Explanation of your planning"
}}
            """

            response_text = self._chat(
                system_prompt="You are a helpful task planning assistant. Return ONLY valid JSON, without any markdown formatting or explanations.",
                user_prompt=prompt
            )

            clean_json = self._extract_json(response_text)
            reasoning_data = json.loads(clean_json)
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
        """Generate a summary of task execution."""
        try:
            prompt = f"""
You are a summary generator. Given a task and its execution results, create a concise summary.

TASK: {task_title}
TASK DESCRIPTION: {task_description}
EXECUTION RESULTS: {json.dumps(execution_results)}

Return ONLY valid JSON:
{{
  "summary": "Brief summary of task and results",
  "key_points": ["point1", "point2", "point3"],
  "status": "completed/failed/in_progress",
  "next_actions": ["action1", "action2"],
  "notes": "Any additional notes"
}}
            """

            response_text = self._chat(
                system_prompt="You are a helpful summary assistant. Return ONLY valid JSON, without any markdown formatting or explanations.",
                user_prompt=prompt
            )

            clean_json = self._extract_json(response_text)
            summary_data = json.loads(clean_json)
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
        """Retrieve memory context for a task."""
        try:
            prompt = f"""
You are a memory retrieval agent. Given a query, retrieve similar past tasks and their outcomes.

QUERY: {query}
SIMILAR_TASKS: {json.dumps(similar_tasks) if similar_tasks else "[]"}

Return ONLY valid JSON:
{{
  "similar_approaches": ["approach1", "approach2"],
  "pitfalls_to_avoid": ["pitfall1", "pitfall2"],
  "best_practices": ["practice1", "practice2"],
  "confidence": 0.85
}}
            """

            response_text = self._chat(
                system_prompt="You are a helpful memory retrieval assistant. Return ONLY valid JSON, without any markdown formatting or explanations.",
                user_prompt=prompt
            )

            clean_json = self._extract_json(response_text)
            memory_data = json.loads(clean_json)
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
        """Get information about the current LLM model."""
        return {
            "model": self.model,
            "temperature": str(self.temperature),
            "max_tokens": str(self.max_tokens),
            "provider": "Ollama"
        }