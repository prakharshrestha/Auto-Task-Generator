"""
Prompt templates for LLM interactions.
"""

TASK_EXTRACTION_PROMPT = """
You are an expert task extraction AI. Your job is to read an email and extract actionable tasks from it.

EMAIL SUBJECT: {email_subject}
EMAIL BODY:
{email_body}
SENDER: {sender}

Please analyze this email and extract all actionable tasks. For each task, provide:
1. Title: A concise task name
2. Description: Detailed description of what needs to be done
3. Priority: low, medium, high, or urgent (based on email urgency indicators)
4. Due Date: If mentioned, in ISO format (YYYY-MM-DD). If not mentioned, use "not_specified"
5. Assigned To: Who should do this task (if mentioned)
6. Tags: Relevant tags to categorize the task

Return the response as a JSON object with the following structure:
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

Important guidelines:
- Extract ONLY actionable tasks (avoid generic statements)
- Be specific and clear
- If no tasks are found, return an empty tasks array
- Confidence should be a number between 0 and 1
- Focus on extracting the core action items
"""

TASK_REASONING_PROMPT = """
You are an intelligent task reasoning and planning agent. Given a task, you need to decide:
1. What workflow steps are needed to complete this task
2. What tools/APIs are needed
3. What information is required
4. Priority level and urgency

TASK: {task_title}
TASK DESCRIPTION: {task_description}
CURRENT CONTEXT: {context}

Please provide your reasoning in the following JSON format:
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

TASK_EXECUTION_PROMPT = """
You are a task execution coordinator. Based on the workflow plan, you will execute each step.

TASK: {task_title}
STEP: {step_number} - {step_action}
AVAILABLE_TOOLS: {available_tools}

Execute this step and provide:
1. Action taken
2. Result/Output
3. Status: success or failed
4. Next recommended step (if any)

Respond in JSON format:
{{
    "step_number": 1,
    "action_taken": "description",
    "result": "output or result",
    "status": "success",
    "output_data": {{}},
    "next_step": "description of next step or null"
}}
"""

SUMMARY_GENERATION_PROMPT = """
You are a summary generator. Given a task and its execution results, create a concise summary.

TASK: {task_title}
TASK DESCRIPTION: {task_description}
EXECUTION RESULTS: {execution_results}

Generate a professional summary in the following JSON format:
{{
    "summary": "Brief summary of task and results",
    "key_points": ["point1", "point2", "point3"],
    "status": "completed/failed/in_progress",
    "next_actions": ["action1", "action2"],
    "notes": "Any additional notes"
}}
"""

MEMORY_RETRIEVAL_PROMPT = """
You are a memory retrieval agent. Given a query, retrieve similar past tasks and their outcomes.

QUERY: {query}
SIMILAR_TASKS: {similar_tasks}

Based on the similar tasks provided, suggest:
1. Similar approaches that worked before
2. Potential pitfalls to avoid
3. Best practices to follow

Respond in JSON format:
{{
    "similar_approaches": ["approach1", "approach2"],
    "pitfalls_to_avoid": ["pitfall1", "pitfall2"],
    "best_practices": ["practice1", "practice2"],
    "confidence": 0.85
}}
"""

# Prompt for general task understanding
TASK_UNDERSTANDING_PROMPT = """
You are a task understanding expert. Analyze the following task and provide a detailed understanding.

TASK: {task}

Provide:
1. Core objective
2. Key requirements
3. Constraints
4. Success criteria
5. Potential challenges

Return as JSON:
{{
    "core_objective": "...",
    "key_requirements": ["req1", "req2"],
    "constraints": ["constraint1"],
    "success_criteria": ["criteria1"],
    "potential_challenges": ["challenge1"]
}}
"""