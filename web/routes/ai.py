from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from web.auth import get_current_user
from web.dependencies import get_command_service, get_ai_service
from services import CommandService, AIService

router = APIRouter(prefix="/ai", tags=["AI"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/", response_class=HTMLResponse)
async def ai_chat(request: Request, user: dict = Depends(get_current_user)):
    """AI Chat interface"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("ai_chat_.html", {"request": request, "user": user})

@router.post("/api/chat")
async def chat(
    request: Request,
    command_service: CommandService = Depends(get_command_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Handle chat messages
    Routes through command service first, then AI service
    """
    data = await request.json()
    message = data.get("message")
    use_cloud = data.get("use_cloud", False)
    provider = data.get("provider", "openai")
    
    cmd_result = command_service.parse_and_execute(message)
    if cmd_result and cmd_result.get("success"):
        return {"response": cmd_result["response"]}
    
    response = await ai_service.generate_response(
        message=message,
        use_cloud=use_cloud,
        provider=provider if use_cloud else None
    )
    
    return {"response": response}

@router.get("/api/mode")
async def get_mode(ai_service: AIService = Depends(get_ai_service)):
    """Get current AI mode"""
    return {"mode": ai_service.get_mode()}

@router.get("/api/status")
async def get_status(ai_service: AIService = Depends(get_ai_service)):
    """Get AI system status"""
    return ai_service.get_status()
