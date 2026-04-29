import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from app.presentation.api import auth, drawings
from app.db.database import init_db

# Доменні помилки
from app.domain.exceptions.exceptions import (
    DomainException,
    EntityNotFoundError,
    InvariantViolationError
)

# === ІМПОРТИ ДЛЯ ЛАБИ 4 (Event Bus та Підписники) ===
from app.infrastructure.events.bus import event_bus
from app.domain.events.events import DrawingCreatedEvent
from app.auxiliary.notifications.service import notification_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Social Drawing Platform")

# Глобальні обробники помилок (з Лаби 2)
@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content={"message": str(exc), "error_type": "Not Found"})

@app.exception_handler(InvariantViolationError)
async def invariant_violation_handler(request: Request, exc: InvariantViolationError):
    return JSONResponse(status_code=400, content={"message": str(exc), "error_type": "Bad Request"})

@app.exception_handler(DomainException)
async def domain_error_handler(request: Request, exc: DomainException):
    return JSONResponse(status_code=400, content={"message": str(exc), "error_type": "Domain Error"})

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@app.on_event("startup")
def on_startup():
    init_db()
    # Підписуємо допоміжний компонент на подію "Малюнок створено"
    event_bus.subscribe(DrawingCreatedEvent, notification_service.handle_drawing_created_event)

app.include_router(auth.router)
app.include_router(drawings.router)

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
    return templates.TemplateResponse(request=request, name="profile.html", context={"user_id": "me"})

@app.get("/profile/{user_id}", response_class=HTMLResponse)
async def view_profile_page(request: Request, user_id: int):
    return templates.TemplateResponse(request=request, name="profile.html", context={"user_id": user_id})

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    return templates.TemplateResponse(request=request, name="search.html")
