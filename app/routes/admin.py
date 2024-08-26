from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Jubilea, Personen, Families, Gebruikers  # Voeg andere modellen toe indien nodig
from ..auth import role_required

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MODEL_MAP = {
    'jubilea': Jubilea,
    'personen': Personen,
    'families': Families,
}

@router.get("/change-owner", response_class=HTMLResponse)
@role_required("Administrator")
async def change_owner(
    request: Request,
    model: str = Query(None),
    page: int = Query(1, ge=1),
    session: Session = Depends(get_session)
):
    items = []
    if model and model in MODEL_MAP:
        query = select(MODEL_MAP[model], Gebruikers).join(Gebruikers, MODEL_MAP[model].created_by == Gebruikers.id)
        items = session.exec(query.offset((page - 1) * 10).limit(10)).all()
    
    return templates.TemplateResponse("change_owner.html", {
        "request": request,
        "models": MODEL_MAP.keys(),
        "selected_model": model,
        "items": items,
        "page": page,
    })