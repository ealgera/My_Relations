from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
from ..database import get_session
from ..models.models import Jubilea, Personen, Jubileumtypes
from datetime import datetime
from typing import Optional
from ..auth import login_required, role_required, get_current_user
from ..logging_config import app_logger

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, name="list_jubilea")
@login_required
async def list_jubilea(request: Request, session: Session = Depends(get_session),
    sort: str = Query(None, description="Sorteer op: jubileumtype, jubileumdag, of persoon")
):
    query = select(Jubilea, Jubileumtypes, Personen).outerjoin(Personen).join(Jubileumtypes)
    
    if sort == "jubileumtype":
        query = query.order_by(Jubileumtypes.naam)
    elif sort == "jubileumdag":
        query = query.order_by(Jubilea.jubileumdag)
    elif sort == "persoon":
        query = query.order_by(func.coalesce(Personen.voornaam, ''), func.coalesce(Personen.achternaam, ''))
    
    results = session.exec(query).all()
    
    jubilea = [
        {
            "id": jubileum.id,
            "jubileumdag": jubileum.jubileumdag,
            "omschrijving": jubileum.omschrijving,
            "jubileumtype": jubileumtype.naam,
            "persoon": f"{persoon.voornaam} {persoon.achternaam}" if persoon else None
        }
        for jubileum, jubileumtype, persoon in results
    ]
    
    return templates.TemplateResponse("jubilea.html", {
        "request": request, 
        "jubilea": jubilea,
        "current_sort": sort
    })

@router.get("/new", name="new_jubileum")
@login_required
async def new_jubileum(request: Request, session: Session = Depends(get_session),
    persoon_id: int = Query(None)
):
    personen = session.exec(select(Personen)).all()
    jubileumtypes = session.exec(select(Jubileumtypes)).all()
    return templates.TemplateResponse("jubileum_form.html", {
        "request": request, 
        "personen": personen,
        "jubileumtypes": jubileumtypes,
        "selected_persoon_id": persoon_id
    })

@router.post("/new", name="create_jubileum")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def create_jubileum(
    request: Request,
    jubileumtype_id: int     = Form(...),
    jubileumdag    : str     = Form(...),
    omschrijving   : str     = Form(None),
    persoon_id     : Optional[int] = Form(None),
    current_user   : dict    = Depends(get_current_user),
    session        : Session = Depends(get_session)
):
    jubileumdag = datetime.strptime(jubileumdag, "%d-%m-%Y").strftime("%Y-%m-%d")
    
    new_jubileum = Jubilea(jubileumtype_id=jubileumtype_id, jubileumdag=jubileumdag, omschrijving=omschrijving, 
        persoon_id=persoon_id, created_by=current_user['id'])
    session.add(new_jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)

@router.get("/{jubileum_id}/edit", name="edit_jubileum")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def edit_jubileum(request: Request, jubileum_id: int, session: Session = Depends(get_session)):
    app_logger.debug(f"[FUNCTION] edit_jubileum: Jubileum ID: {jubileum_id}")
    jubileum = session.get(Jubilea, jubileum_id)
    app_logger.debug(f"Jubileum: {jubileum}")
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    personen = session.exec(select(Personen)).all()
    jubileumtypes = session.exec(select(Jubileumtypes)).all()

    formatted_date = datetime.strptime(jubileum.jubileumdag, "%Y-%m-%d").strftime("%d-%m-%Y")
    
    return templates.TemplateResponse("jubileum_form.html", {
        "request": request, 
        "jubileum": jubileum,
        "personen": personen,
        "jubileumtypes": jubileumtypes,
        "formatted_date": formatted_date
    })

@router.post("/{jubileum_id}/edit", name="update_jubileum")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def update_jubileum(
    request: Request,
    jubileum_id    : int,
    jubileumtype_id: int     = Form(...),
    jubileumdag    : str     = Form(...),
    omschrijving   : str     = Form(None),
    persoon_id     : Optional[int] = Form(None),
    session        : Session = Depends(get_session)
):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    
    jubileumdag = datetime.strptime(jubileumdag, "%d-%m-%Y").strftime("%Y-%m-%d")
    
    jubileum.jubileumtype_id = jubileumtype_id
    jubileum.jubileumdag     = jubileumdag
    jubileum.omschrijving    = omschrijving
    jubileum.persoon_id      = persoon_id
    
    session.add(jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)

@router.get("/{jubileum_id}/delete", name="delete_jubileum")
@login_required
@role_required(["Administrator", "Beheerder"])
async def delete_jubileum(request: Request, jubileum_id: int, session: Session = Depends(get_session)):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    session.delete(jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)
