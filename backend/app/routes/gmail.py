import re
from fastapi import APIRouter, HTTPException

from app.services.gmail_oauth_service import GmailOAuthService
from app.services.gmail_service import GmailService
from app.agents.task_agent import TaskAgent

router = APIRouter(prefix="/api/gmail", tags=["gmail"])

agent = TaskAgent()


def _clean_body(text: str, max_len: int = 2000) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _is_promotional_or_newsletter(msg: dict) -> bool:
    labels = msg.get("labels", [])
    if "CATEGORY_PROMOTIONS" in labels or "CATEGORY_SOCIAL" in labels:
        return True

    sender_email = (msg.get("from_email") or "").lower()
    promotional_prefixes = ("noreply", "no-reply", "marketing", "news", "newsletter", "updates", "info", "hello")
    if sender_email.split("@")[0] in promotional_prefixes or "newsletter" in sender_email:
        return True

    body = msg.get("body", "").lower()
    # Simple heuristic: presence of unsubscribe link usually implies newsletter/marketing
    if "unsubscribe" in body and len(body) > 100:
        return True

    return False


@router.get("/recent")
def recent_emails(limit: int = 8):
    limit = min(max(limit, 1), 8)

    oauth = GmailOAuthService()
    email, creds = oauth.load_latest_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="No Gmail token found. Login at /auth/google/login")

    gmail = GmailService(creds)
    messages = gmail.list_latest(max_results=limit)

    items = [gmail.get_message(m["id"]) for m in messages]
    return {
        "email": email,
        "count": len(items),
        "messages": items
    }


@router.get("/recent-plans")
def recent_email_plans(limit: int = 8, mode: str = "plan"):
    """
    mode = raw | extract | plan
    raw: no LLM
    extract: task extraction only
    plan: extract + reasoning
    """
    limit = min(max(limit, 1), 8)

    oauth = GmailOAuthService()
    account_email, creds = oauth.load_latest_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="No Gmail token found. Login at /auth/google/login")

    gmail = GmailService(creds)
    messages = gmail.list_latest(max_results=limit)
    items = [gmail.get_message(m["id"]) for m in messages]

    grouped = {}

    for msg in items:
        if _is_promotional_or_newsletter(msg):
            continue

        sender_key = msg.get("from_email") or msg.get("from") or "unknown"

        if sender_key not in grouped:
            grouped[sender_key] = {
                "sender_email": msg.get("from_email"),
                "sender_name": msg.get("from_name"),
                "from_raw": msg.get("from"),
                "emails": []
            }

        clean_body = _clean_body(msg.get("body", ""), max_len=800)

        email_entry = {
            "id": msg.get("id"),
            "subject": msg.get("subject"),
            "date": msg.get("date"),
            "body": clean_body,
            "tasks": [],
            "plans": []
        }

        if mode == "raw":
            grouped[sender_key]["emails"].append(email_entry)
            continue

        extraction = agent.process_email(
            email_subject=msg.get("subject", ""),
            email_body=clean_body,
            sender=msg.get("from")
        )

        email_entry["tasks"] = extraction.get("tasks", [])
        email_entry["extraction_summary"] = extraction.get("summary")
        email_entry["confidence"] = extraction.get("confidence")

        if mode == "extract":
            grouped[sender_key]["emails"].append(email_entry)
            continue

        for task in extraction.get("tasks", []):
            task_id = task.get("id")
            if task_id:
                plan = agent.reason_and_plan_task(task_id)
            else:
                plan = {"success": False, "error": "Task id missing"}

            email_entry["plans"].append(plan)

        grouped[sender_key]["emails"].append(email_entry)

    return {
        "email": account_email,
        "count": len(items),
        "mode": mode,
        "senders": list(grouped.values())
    }