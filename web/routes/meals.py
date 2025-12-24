from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core import Phenom
from web.auth import get_current_user

router = APIRouter(prefix="/meals", tags=["Meals"])
templates = Jinja2Templates(directory="web/templates")
phenom = Phenom()

@router.get("/", response_class=HTMLResponse)
async def meals_page(request: Request, user: dict = Depends(get_current_user)):
    meals = list(phenom.meal_planner.meals.values())
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("meals_.html", {"request": request, "user": user, "meals": meals})

@router.post("/api/add")
async def add_meal(request: Request):
    data = await request.json()
    meal = phenom.meal_planner.add_meal(data.get("name"), data.get("meal_type", "lunch"))
    return meal

@router.get("/api/all")
async def get_meals():
    return list(phenom.meal_planner.meals.values())
