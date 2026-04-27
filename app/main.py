import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.presentation.api import auth, drawings
from app.db.database import init_db

# === ІМПОРТУЄМО НАШІ ДОМЕННІ ПОМИЛКИ ===
from app.domain.exceptions.exceptions import (
    DomainException,
    EntityNotFoundError,
    InvariantViolationError
)

# Get the base directory for paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Social Drawing Platform")

# === ДОДАЄМО ГЛОБАЛЬНІ ОБРОБНИКИ ПОМИЛОК ===

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    """Перехоплює помилки 'не знайдено' і повертає 404"""
    return JSONResponse(
        status_code=404,
        content={"message": str(exc), "error_type": "Not Found"}
    )

@app.exception_handler(InvariantViolationError)
async def invariant_violation_handler(request: Request, exc: InvariantViolationError):
    """
    Перехоплює всі бізнес-помилки (валідація, дублікати email/nickname) 
    і автоматично повертає 400 Bad Request
    """
    return JSONResponse(
        status_code=400,
        content={"message": str(exc), "error_type": "Business Rule Violation"}
    )

@app.exception_handler(DomainException)
async def fallback_domain_handler(request: Request, exc: DomainException):
    """Фолбек для будь-яких інших доменних помилок, які ми могли пропустити"""
    return JSONResponse(
        status_code=400,
        content={"message": str(exc), "error_type": "Domain Error"}
    )

# ==========================================

# Templates with absolute path
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Initialize DB (create tables)
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth.router)
app.include_router(drawings.router)

# Serve static files with absolute path
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/drawing/new", response_class=HTMLResponse)
async def create_drawing_page(request: Request):
    return templates.TemplateResponse(request=request, name="drawing.html", context={"drawing_id": "new"})

@app.get("/drawing/{drawing_id}", response_class=HTMLResponse)
async def edit_drawing_page(request: Request, drawing_id: str):
    return templates.TemplateResponse(request=request, name="drawing.html", context={"drawing_id": drawing_id})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse(request=request, name="profile.html", context={"target_user_id": None})

@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def view_profile_page(request: Request, user_id: int):
    return templates.TemplateResponse(request=request, name="profile.html", context={"target_user_id": user_id})

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    return templates.TemplateResponse(request=request, name="search.html")
