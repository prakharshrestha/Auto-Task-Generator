"""
Google OAuth routes for Gmail.
"""
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.gmail_oauth_service import GmailOAuthService

from config import settings

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
            return RedirectResponse(f"{settings.frontend_url}/?login=error&error=Missing+code")

        oauth = GmailOAuthService()
        creds = oauth.exchange_code(code)
        userinfo = oauth.get_userinfo(creds.token)
        email = userinfo.get("email")

        if not email:
            return RedirectResponse(f"{settings.frontend_url}/?login=error&error=Could+not+retrieve+email")

        oauth.store_credentials(email, creds)

        return RedirectResponse(f"{settings.frontend_url}/?login=success&email={email}")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        import urllib.parse
        error_msg = urllib.parse.quote_plus(str(e))
        return RedirectResponse(f"{settings.frontend_url}/?login=error&error={error_msg}")


@router.get("/status")
async def google_status():
    try:
        oauth = GmailOAuthService()
        email, creds = oauth.load_latest_credentials()
        if creds:
            return JSONResponse({
                "connected": True,
                "email": email
            })
        return JSONResponse({
            "connected": False
        })
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return JSONResponse({
            "connected": False,
            "error": str(e)
        })


@router.post("/logout")
async def google_logout():
    try:
        oauth = GmailOAuthService()
        oauth.clear_credentials()
        return JSONResponse({
            "success": True,
            "message": "Logged out successfully"
        })
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))