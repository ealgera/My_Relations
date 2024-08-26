from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Personen, Families, Gebruikers
from ..auth import login_required, role_required, get_current_user, owner_or_admin_required
from ..logging_config import app_logger
from datetime import datetime

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_personen(request: Request, session: Session = Depends(get_session),
    sort: str = Query(None, description="Sorteer op: voornaam, achternaam, of familie")
):
    query = select(Personen).join(Families)
    
    if sort == "voornaam":
        query = query.order_by(Personen.voornaam)
    elif sort == "achternaam":
        query = query.order_by(Personen.achternaam)
    elif sort == "familie":
        query = query.order_by(Families.familienaam)
    
    personen = session.exec(query).all()
    
    return templates.TemplateResponse("personen.html", {
        "request": request, 
        "personen": personen,
        "current_sort": sort
    })

@router.get("/new", name="new_persoon")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def new_persoon(request: Request, session: Session = Depends(get_session)):
    families = session.exec(select(Families)).all()
    return templates.TemplateResponse("persoon_form.html", {"request": request, "families": families, "persoon": None})

@router.post("/new", name="create_persoon")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def create_persoon(
    request     : Request,
    voornaam    : str     = Form(...),
    achternaam  : str     = Form(...),
    familie_id  : int     = Form(...),
    leeft       : bool    = Form(False),
    current_user: dict    = Depends(get_current_user),
    session     : Session = Depends(get_session)):

    new_persoon = Personen(voornaam=voornaam, achternaam=achternaam, familie_id=familie_id,
        leeft=leeft,created_by=current_user['id'])
    session.add(new_persoon)
    session.commit()
    return RedirectResponse(url="/personen", status_code=303)

@router.get("/{persoon_id}/edit", name="edit_persoon")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
@owner_or_admin_required(Personen)
async def edit_persoon(request: Request, persoon_id: int, session: Session = Depends(get_session)):
    persoon = session.get(Personen, persoon_id)
    
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    
    families = session.exec(select(Families)).all()

    # Sorteer de jubilea op datum
    sorted_jubilea = sorted(persoon.jubilea, key=lambda x: datetime.strptime(x.jubileumdag, "%Y-%m-%d"))
    
    return templates.TemplateResponse("persoon_form.html", {
        "request" : request, 
        "persoon" : persoon, 
        "families": families,
        "jubilea" : sorted_jubilea
    })

@router.post("/{persoon_id}/edit", name="update_persoon")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
@owner_or_admin_required(Personen)
async def update_persoon(
    request: Request,
    persoon_id  : int,
    voornaam    : str        = Form(...),
    achternaam  : str        = Form(...),
    familie_id  : int        = Form(...),
    leeft       : bool       = Form(False),
    current_user: Gebruikers = Depends(get_current_user),
    session     : Session    = Depends(get_session)
):
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    # if persoon.created_by != current_user['id']: # and current_user.role != "admin":
        # raise HTTPException(status_code=403, detail="Geen toestemming om deze familie te bewerken")

    persoon.voornaam   = voornaam
    persoon.achternaam = achternaam
    persoon.familie_id = familie_id
    persoon.leeft = leeft

    session.add(persoon)
    session.commit()
    return RedirectResponse(url="/personen", status_code=303)

@router.get("/{persoon_id}/delete", name="delete_persoon")
async def delete_persoon(persoon_id: int, session: Session = Depends(get_session)):
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    session.delete(persoon)
    session.commit()
    return RedirectResponse(url="/personen", status_code=303)
