"""
Google OAuth routes for Gmail.
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.gmail_oauth_service import GmailOAuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/login")
async def google_login():
    try:
        oauth = GmailOAuthService()
        url = oauth.get_auth_url()
        return RedirectResponse(url)
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/callback")
async def google_callback(request: Request):
    try:
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Missing code")

        oauth = GmailOAuthService()
        creds = oauth.exchange_code(code)
        userinfo = oauth.get_userinfo(creds.token)
        email = userinfo.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Could not get user email")

        oauth.store_credentials(email, creds)

        return JSONResponse({
            "success": True,
            "email": email,
            "message": "OAuth login successful. Token stored."
        })

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))