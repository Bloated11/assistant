from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.auth import get_current_user
from web.dependencies import get_system_service
from services import SystemService

router = APIRouter(prefix="/system", tags=["System"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/status", response_class=HTMLResponse)
async def system_status_page(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """System status dashboard page"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("system_status.html", {"request": request, "user": user})

@router.get("/api/status")
async def get_system_status(
    system_service: SystemService = Depends(get_system_service)
):
    """Get system status API"""
    return system_service.get_system_status()
