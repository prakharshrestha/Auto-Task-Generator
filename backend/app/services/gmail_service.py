import base64
from email.utils import parseaddr
from typing import List, Dict, Any

from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GmailService:
    def __init__(self, creds: Credentials):
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        self.service = build("gmail", "v1", credentials=creds)

    def list_latest(self, max_results: int = 8) -> List[Dict[str, Any]]:
        resp = self.service.users().messages().list(
            userId="me",
            maxResults=max_results
        ).execute()
        return resp.get("messages", [])

    def get_message(self, message_id: str) -> Dict[str, Any]:
        msg = self.service.users().messages().get(
            userId="me",
            id=message_id,
            format="full"
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        from_raw = headers.get("from", "")
        name, email = parseaddr(from_raw)

        subject = headers.get("subject", "")
        date = headers.get("date", "")
        body = self._extract_body(msg.get("payload", {}))

        return {
            "id": message_id,
            "from": from_raw,
            "from_name": name,
            "from_email": email,
            "subject": subject,
            "date": date,
            "body": body
        }

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        if payload.get("body", {}).get("data"):
            return self._decode(payload["body"]["data"])

        for part in payload.get("parts", []):
            if part.get("mimeType", "").startswith("text/plain") and part.get("body", {}).get("data"):
                return self._decode(part["body"]["data"])
            if part.get("parts"):
                nested = self._extract_body(part)
                if nested:
                    return nested
        return ""

    def _decode(self, data: str) -> str:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="ignore")