from fastapi import FastAPI, Depends, Request, HTTPException, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pathlib import Path
from .database import get_session, create_db_and_tables, engine
from .models.models import Families, Personen, Jubilea, Relatietypes, Relaties, Jubileumtypes
from datetime import date
from dateutil.relativedelta import relativedelta
from .routes import families, relatietypes, jubilea, personen, relaties, jubileumtypes, gebruikers, admin
from .logging_config import app_logger, log_info, log_debug
from .auth import router as auth_router, login_required #, AuthMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
import os

settings = get_settings()
log_info("[MAIN] Applicatie My_Relations gestart...")
log_debug(f"[MAIN] Settings: {settings}")

app = FastAPI()

# Monteer de static directory
base_path = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=base_path / "static"), name="static")
templates = Jinja2Templates(directory=base_path / "templates")

# Monteer de foto directory
foto_path = Path(settings.FOTO_DIR)
print(f"FOTO_DIR path: {foto_path}")
print(f"FOTO_DIR exists: {foto_path.exists()}")
print(f"FOTO_DIR is directory: {foto_path.is_dir()}")
print(f"FOTO_DIR permissions: {oct(os.stat(foto_path).st_mode)[-3:]}")
print(f"Current process UID: {os.getuid()}")
print(f"Current process GID: {os.getgid()}")

if not foto_path.exists():
    try:
        foto_path.mkdir(parents=True, exist_ok=True)
        print(f"Created FOTO_DIR: {foto_path}")
    except Exception as e:
        print(f"Error creating FOTO_DIR: {str(e)}")

if os.access(foto_path, os.W_OK):
    print(f"FOTO_DIR is writable: {foto_path}")
else:
    print(f"WARNING: FOTO_DIR is not writable: {foto_path}")
# app.mount("/fotos", StaticFiles(directory=str(settings.FOTO_DIR)), name="fotos")
app.mount("/fotos", StaticFiles(directory=settings.FOTO_DIR), name="fotos")

# Voeg SessionMiddleware toe
log_info("[MAIN] Adding SessionMiddleware")
# app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="my_relations_session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)
log_info("[MAIN] Adding CORSMiddleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pas dit aan naar je specifieke domein in productie
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app_logger.debug("Adding AuthMiddleware")
# app.add_middleware(AuthMiddleware)

# Inclusie van de diverse blueprints
app.include_router(families.router, prefix="/families", tags=["families"])
app.include_router(relatietypes.router, prefix="/relatietypes", tags=["relatietypes"])
app.include_router(jubilea.router, prefix="/jubilea", tags=["jubilea"])
app.include_router(personen.router, prefix="/personen", tags=["personen"])
app.include_router(relaties.router, prefix="/relaties", tags=["relaties"])
app.include_router(jubileumtypes.router, prefix="/jubileumtypes", tags=["jubileumtypes"])
app.include_router(gebruikers.router, prefix="/users", tags=["gebruikers"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

app.include_router(auth_router, tags=["auth"])

@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

# @app.on_event("startup")
# async def print_routes():
#     routes = [route for route in app.router.routes]
#     for route in routes:
#         print(f"Route name: {route.name}, path: {route.path}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303 and exc.detail == "Not authenticated":
        return RedirectResponse(url='/')
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "detail": exc.detail, "status_code": exc.status_code},
        status_code=exc.status_code
    )

@app.get("/check-session")
async def check_session(request: Request):
    if 'session' in request.scope:
        return {"session_exists": True, "session_data": request.session}
    else:
        return {"session_exists": False}

# def get_upcoming_events(session: Session):
#     today = date.today()
#     end_date = today + relativedelta(months=1)
    
#     jubilea = session.exec(
#         select(Jubilea, Personen, Jubileumtypes)
#         .outerjoin(Personen)
#         .join(Jubileumtypes)
#     ).all()
    
#     upcoming_events = []
#     for jubileum, persoon, jubileumtype in jubilea:
#         event_date = date.fromisoformat(jubileum.jubileumdag)
#         this_year_event = event_date.replace(year=today.year)
#         if this_year_event < today:
#             this_year_event = this_year_event.replace(year=today.year + 1)
        
#         if today <= this_year_event <= end_date:
#             if jubileumtype.naam == "Geboortedag" and persoon:
#                 age = this_year_event.year - event_date.year
#                 if persoon.leeft:
#                     event_description = f"wordt {age} jaar"
#                 else:
#                     event_description = f"zou {age} jaar zijn geworden."
#             else:
#                 event_description = jubileumtype.naam
            
#             if persoon:
#                 name = f"{persoon.voornaam} {persoon.achternaam}"
#             else:
#                 name = jubileum.omschrijving or "Herdenking"
            
#             upcoming_events.append({
#                 "name": name,
#                 "date": this_year_event,
#                 "event_type": jubileumtype.naam,
#                 "description": event_description
#             })
    
#     return sorted(upcoming_events, key=lambda x: x['date'])

def get_upcoming_events(session: Session):
    today = date.today()
    end_date = today + relativedelta(months=1)
    
    jubilea = session.exec(
        select(Jubilea, Personen, Jubileumtypes)
        .outerjoin(Personen)
        .join(Jubileumtypes)
    ).all()
    
    upcoming_events = []
    for jubileum, persoon, jubileumtype in jubilea:
        event_date = date.fromisoformat(jubileum.jubileumdag)
        this_year_event = event_date.replace(year=today.year)
        if this_year_event < today:
            this_year_event = this_year_event.replace(year=today.year + 1)
        
        if today <= this_year_event <= end_date:
            if jubileumtype.naam == "Geboortedag" and persoon:
                age = this_year_event.year - event_date.year
                if persoon.leeft:
                    event_description = f"wordt {age} jaar"
                else:
                    event_description = f"zou {age} jaar zijn geworden."
            else:
                event_description = jubileumtype.naam
            
            if persoon:
                name = f"{persoon.voornaam} {persoon.achternaam}"
                foto_url = persoon.foto_url
            else:
                name = jubileum.omschrijving or "Herdenking"
                foto_url = jubileum.foto_url
            
            upcoming_events.append({
                "jubileum_id": jubileum.id,
                "name": name,
                "date": this_year_event,
                "event_type": jubileumtype.naam,
                "description": event_description,
                "foto_url": foto_url
            })
    
    return sorted(upcoming_events, key=lambda x: x['date'])

@app.get("/", response_class=HTMLResponse)
async def welcome(
    request: Request,
    error: str = Query(None),
    email: str = Query(None)
):
    log_info("[MAIN] Handling request to /")
    if 'user' in request.session:
        return RedirectResponse(url='/home', status_code=303)
    return templates.TemplateResponse("welcome.html", {
        "request": request,
        "error": error,
        "email": email
    })                                                                                                             

@app.get("/home", response_class=HTMLResponse)
@login_required
async def home(request: Request, session: Session = Depends(get_session)):
    log_info("[MAIN] Handling request to /home")
    
    # Implementeer hier je bestaande home-logica
    upcoming_events = get_upcoming_events(session)
    auth_error = request.cookies.get("auth_error")

    response = templates.TemplateResponse("index.html", {
        "request": request,
        "upcoming_events": upcoming_events,
        "auth_error": auth_error
    })   

    if auth_error:
        response.delete_cookie("auth_error")

    return response

@app.get("/protected-route")
@login_required
async def protected_route(request: Request):
    user = request.session.get('user')
    return {"message": f"Hello, {user['name']}! This is a protected route."}

@app.get("/test-session")
async def test_session(request: Request):
    if "count" not in request.session:
        request.session["count"] = 0
    request.session["count"] += 1
    return {"count": request.session["count"]}

@app.get("/check-session")
async def check_session(request: Request):
    return {
        "session_exists": "session" in request.scope,
        "session_data": request.scope.get("session", {}),
        "cookies": request.cookies
    }

@app.get("/debug-headers")
async def debug_headers(request: Request):
    return {
        "headers": dict(request.headers),
        "cookies": request.cookies
    }

@app.get("/test-logs-url")
async def test_logs_url(request: Request):
    return {"url": request.url_for("view_logs")}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)