from fastapi import FastAPI, Depends, Request, HTTPException, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pathlib import Path
from .database import get_session, create_db_and_tables
from .models.models import Families, Personen, Jubilea, Relatietypes, Relaties
from datetime import date
from dateutil.relativedelta import relativedelta
from .routes import families, relatietypes, jubilea, personen

import logging 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Monteer de static directory
base_path = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=base_path / "static"), name="static")
templates = Jinja2Templates(directory=base_path / "templates")

# Inclusie van de diverse blueprints
app.include_router(families.router, prefix="/families", tags=["families"])
app.include_router(relatietypes.router, prefix="/relatietypes", tags=["relatietypes"])
app.include_router(jubilea.router, prefix="/jubilea", tags=["jubilea"])
app.include_router(personen.router, prefix="/personen", tags=["personen"])

@app.on_event("startup")
async def startup_event():
    create_db_and_tables()

def get_upcoming_events(session: Session):
    today = date.today()
    end_date = today + relativedelta(months=1)
    
    jubilea = session.exec(
        select(Jubilea)
        .join(Personen)
    ).all()
    
    upcoming_events = []
    for jubileum in jubilea:
        event_date = date.fromisoformat(jubileum.jubileumdag)
        this_year_event = event_date.replace(year=today.year)
        if this_year_event < today:
            this_year_event = this_year_event.replace(year=today.year + 1)
        
        if today <= this_year_event <= end_date:
            if jubileum.jubileumnaam == "Geboortedag":
                age = this_year_event.year - event_date.year
                event_description = f"wordt {age} jaar"
            else:
                event_description = jubileum.jubileumnaam
            
            upcoming_events.append({
                "name": f"{jubileum.persoon.voornaam} {jubileum.persoon.achternaam}",
                "date": this_year_event,
                "event_type": jubileum.jubileumnaam,
                "description": event_description
            })
    
    return sorted(upcoming_events, key=lambda x: x['date'])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, session: Session = Depends(get_session)):
    upcoming_events = get_upcoming_events(session)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "upcoming_events": upcoming_events
    })                                                                                                                 

@app.get("/healthcheck")
async def healthcheck(session: Session = Depends(get_session)):
    try:
        session.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)