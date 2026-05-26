"""
Gmail OAuth helper: login URL, token exchange, store tokens in SQLite.
"""
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from config import settings

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly"
]


class GmailOAuthService:
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri

        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise RuntimeError("Google OAuth env vars not set")

        self.db_path = self._extract_sqlite_path(settings.database_url)
        self._init_db()

    def _extract_sqlite_path(self, database_url: str) -> str:
        if database_url.startswith("sqlite:///"):
            return database_url.replace("sqlite:///", "")
        if database_url.startswith("sqlite://"):
            return database_url.replace("sqlite://", "")
        return "./app.db"

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS gmail_tokens (
                email TEXT PRIMARY KEY,
                refresh_token TEXT,
                access_token TEXT,
                token_uri TEXT,
                client_id TEXT,
                client_secret TEXT,
                scopes TEXT,
                expiry TEXT
            )
            """)
            conn.commit()

    def get_auth_url(self) -> str:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        return auth_url

    def exchange_code(self, code: str) -> Credentials:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )
        flow.fetch_token(code=code)
        return flow.credentials

    def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def store_credentials(self, email: str, creds: Credentials):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            INSERT INTO gmail_tokens (
                email, refresh_token, access_token, token_uri,
                client_id, client_secret, scopes, expiry
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET
                refresh_token=excluded.refresh_token,
                access_token=excluded.access_token,
                token_uri=excluded.token_uri,
                client_id=excluded.client_id,
                client_secret=excluded.client_secret,
                scopes=excluded.scopes,
                expiry=excluded.expiry
            """, (
                email,
                creds.refresh_token,
                creds.token,
                creds.token_uri,
                creds.client_id,
                creds.client_secret,
                json.dumps(creds.scopes),
                creds.expiry.isoformat() if creds.expiry else None
            ))
            conn.commit()

    def load_latest_credentials(self) -> Tuple[Optional[str], Optional[Credentials]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
            SELECT email, refresh_token, access_token, token_uri,
                   client_id, client_secret, scopes, expiry
            FROM gmail_tokens
            ORDER BY rowid DESC
            LIMIT 1
            """).fetchone()

        if not row:
            return None, None

        email, refresh_token, access_token, token_uri, client_id, client_secret, scopes, expiry = row
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=json.loads(scopes) if scopes else None
        )
        if expiry:
            try:
                creds.expiry = datetime.fromisoformat(expiry)
            except ValueError:
                pass

        return email, creds

    def clear_credentials(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM gmail_tokens")
            conn.commit()
        return True