import os
os.environ["NEST_ASYNCIO_SKIP"] = "1"

import asyncio
import sys
import logging

logger = logging.getLogger(__name__)

try:
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
except Exception as e:
    logger.debug(f"Could not set event loop policy: {e}")

from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core import Phenom
from web.auth import create_access_token, get_current_user, verify_password, get_password_hash
from web.database import get_db, User, init_db

app = FastAPI(title="Phenom AI", description="Personal AI Assistant")

app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")

phenom = Phenom()

@app.on_event("startup")
async def startup_event():
    init_db()
    print("✓ Phenom AI Web Server Started")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard_.html", {"request": request, "user": user, "phenom": phenom})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login_.html", {"request": request})

@app.post("/api/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = verify_password(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user["username"]})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=604800,
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register_futuristic.html", {"request": request})

@app.post("/api/register")
async def register(request: Request, response: Response):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    
    db = next(get_db())
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password)
    )
    db.add(user)
    db.commit()
    
    access_token = create_access_token(data={"sub": username})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=604800,
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

from web.routes import ai, tasks, projects, habits, notes, finance, goals, health
from web.routes import reading, meals, learning, time, journal, contacts, travel
from web.routes import reminders, ideas, inventory, quotes, events, archive, system

app.include_router(ai.router)
app.include_router(system.router)
app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(habits.router)
app.include_router(notes.router)
app.include_router(finance.router)
app.include_router(goals.router)
app.include_router(health.router)
app.include_router(reading.router)
app.include_router(meals.router)
app.include_router(learning.router)
app.include_router(time.router)
app.include_router(journal.router)
app.include_router(contacts.router)
app.include_router(travel.router)
app.include_router(reminders.router)
app.include_router(ideas.router)
app.include_router(inventory.router)
app.include_router(quotes.router)
app.include_router(events.router)
app.include_router(archive.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
