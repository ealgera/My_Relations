from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Personen, Families

router = APIRouter()

templates = Jinja2Templates(directory="templates")

# @router.get("/personen", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def list_personen(
    request: Request, 
    session: Session = Depends(get_session),
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

# @router.get("/personen/new", name="new_persoon")
@router.get("/new", name="new_persoon")
async def new_persoon(request: Request, session: Session = Depends(get_session)):
    families = session.exec(select(Families)).all()
    return templates.TemplateResponse("persoon_form.html", {"request": request, "families": families})

# @router.post("/personen/new", name="create_persoon")
@router.post("/new", name="create_persoon")
async def create_persoon(
    request: Request,
    voornaam: str = Form(...),
    achternaam: str = Form(...),
    familie_id: int = Form(...),
    session: Session = Depends(get_session)
):
    new_persoon = Personen(voornaam=voornaam, achternaam=achternaam, familie_id=familie_id)
    session.add(new_persoon)
    session.commit()
    return RedirectResponse(url="/personen", status_code=303)

# @router.get("/personen/{persoon_id}/edit", name="edit_persoon")
@router.get("/{persoon_id}/edit", name="edit_persoon")
async def edit_persoon(persoon_id: int, request: Request, session: Session = Depends(get_session)):
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    families = session.exec(select(Families)).all()
    return templates.TemplateResponse("persoon_form.html", {"request": request, "persoon": persoon, "families": families})

# @router.post("/personen/{persoon_id}/edit", name="update_persoon")
@router.post("/{persoon_id}/edit", name="update_persoon")
async def update_persoon(
    persoon_id: int,
    voornaam: str = Form(...),
    achternaam: str = Form(...),
    familie_id: int = Form(...),
    session: Session = Depends(get_session)
):
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")

    persoon.voornaam = voornaam
    persoon.achternaam = achternaam
    persoon.familie_id = familie_id

    session.add(persoon)
    session.commit()
    return RedirectResponse(url="/personen", status_code=303)

# @router.get("/personen/{persoon_id}/delete", name="delete_persoon")
@router.get("/{persoon_id}/delete", name="delete_persoon")
async def delete_persoon(persoon_id: int, session: Session = Depends(get_session)):
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    session.delete(persoon)
    session.commit()
    return RedirectResponse(url="/personen", status_code=303)
