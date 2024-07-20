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
from .routes import families, relatietypes, jubilea, personen, relaties, jubileumtypes, gebruikers
from .logging_config import app_logger
from .auth import router as auth_router, login_required
from starlette.middleware.sessions import SessionMiddleware
from config import get_settings
# from my_relations_app.config import get_settings
import secrets

settings = get_settings()
# app_logger.debug(f"Settings: {settings}")

app = FastAPI()

# Monteer de static directory
base_path = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=base_path / "static"), name="static")
templates = Jinja2Templates(directory=base_path / "templates")

# Voeg SessionMiddleware toe
# SECRET_KEY = secrets.token_urlsafe(32)  # Genereer een veilige random string voor de secret_key
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Inclusie van de diverse blueprints
app.include_router(families.router, prefix="/families", tags=["families"])
app.include_router(relatietypes.router, prefix="/relatietypes", tags=["relatietypes"])
app.include_router(jubilea.router, prefix="/jubilea", tags=["jubilea"])
app.include_router(personen.router, prefix="/personen", tags=["personen"])
app.include_router(relaties.router, prefix="/relaties", tags=["relaties"])
app.include_router(jubileumtypes.router, prefix="/jubileumtypes", tags=["jubileumtypes"])
app.include_router(gebruikers.router, prefix="/users", tags=["gebruikers"])

app.include_router(auth_router, tags=["auth"])

# @app.on_event("startup")
# async def startup_event():
    # create_db_and_tables()

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
            else:
                name = jubileum.omschrijving or "Herdenking"
            
            upcoming_events.append({
                "name": name,
                "date": this_year_event,
                "event_type": jubileumtype.naam,
                "description": event_description
            })
    
    return sorted(upcoming_events, key=lambda x: x['date'])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    upcoming_events = get_upcoming_events(session)
    auth_error = request.cookies.get("auth_error") # Er is een cookie gezet (in auth.py) voor fout als niet correct geauthentiseerd

    response = templates.TemplateResponse("index.html", {
        "request"        : request,
        "upcoming_events": upcoming_events,
        "auth_error"     : auth_error
    })   

    if auth_error:
        response.delete_cookie("auth_error")  # Verwijder de cookie na gebruik

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)