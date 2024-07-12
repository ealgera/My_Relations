from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Jubilea, Personen
from datetime import date

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", name="list_jubilea")
async def list_jubilea(request: Request, session: Session = Depends(get_session)):
    jubilea = session.exec(select(Jubilea)).all()
    return templates.TemplateResponse("jubilea.html", {"request": request, "jubilea": jubilea})

@router.get("/new", name="new_jubileum")
async def new_jubileum(request: Request, session: Session = Depends(get_session)):
    personen = session.exec(select(Personen)).all()
    return templates.TemplateResponse("jubileum_form.html", {"request": request, "personen": personen})

@router.post("/new", name="create_jubileum")
async def create_jubileum(
    request: Request,
    jubileumnaam: str = Form(...),
    jubileumdag: date = Form(...),
    persoon_id: int = Form(...),
    session: Session = Depends(get_session)
):
    new_jubileum = Jubilea(jubileumnaam=jubileumnaam, jubileumdag=jubileumdag, persoon_id=persoon_id)
    session.add(new_jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)

@router.get("/{jubileum_id}/edit", name="edit_jubileum")
async def edit_jubileum(jubileum_id: int, request: Request, session: Session = Depends(get_session)):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    personen = session.exec(select(Personen)).all()
    
    # Bereid de datum voor
    if isinstance(jubileum.jubileumdag, str):
        formatted_date = jubileum.jubileumdag
    else:
        formatted_date = jubileum.jubileumdag.strftime('%Y-%m-%d')
    
    return templates.TemplateResponse("jubileum_form.html", {
        "request": request, 
        "jubileum": jubileum, 
        "personen": personen,
        "formatted_date": formatted_date
    })

@router.post("/{jubileum_id}/edit", name="update_jubileum")
async def update_jubileum(
    jubileum_id: int,
    jubileumnaam: str = Form(...),
    jubileumdag: date = Form(...),
    persoon_id: int = Form(...),
    session: Session = Depends(get_session)
):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    
    jubileum.jubileumnaam = jubileumnaam
    jubileum.jubileumdag = jubileumdag
    jubileum.persoon_id = persoon_id
    
    session.add(jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)

@router.get("/{jubileum_id}/delete", name="delete_jubileum")
async def delete_jubileum(jubileum_id: int, session: Session = Depends(get_session)):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    session.delete(jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)
