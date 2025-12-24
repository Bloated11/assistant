from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def projects_page(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("projects_.html", {"request": request, "user": user})

@router.post("/api/create")
async def create_project(request: Request):
    data = await request.json()
    project = phenom.project_manager.create_project(
        data.get("name"),
        description=data.get("description", ""),
        deadline=data.get("deadline")
    )
    return project

@router.get("/api/all")
async def get_projects():
    projects_list = phenom.project_manager.list_projects()
    projects_dict = {p['id']: p for p in projects_list}
    return {"projects": projects_dict}

@router.delete("/api/{project_id}")
async def delete_project(project_id: str):
    success = phenom.project_manager.delete_project(project_id)
    return {"success": success}
