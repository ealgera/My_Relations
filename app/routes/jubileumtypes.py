from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Jubileumtypes

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse, name="list_jubileumtypes")
async def list_jubileumtypes(request: Request, session: Session = Depends(get_session)):
    jubileumtypes = session.exec(select(Jubileumtypes)).all()
    return templates.TemplateResponse("jubileumtypes.html", {"request": request, "jubileumtypes": jubileumtypes})

@router.get("/new", response_class=HTMLResponse, name="new_jubileumtype")
async def new_jubileumtype(request: Request):
    return templates.TemplateResponse("jubileumtype_form.html", {"request": request})

@router.post("/new", response_class=HTMLResponse, name="create_jubileumtype")
async def create_jubileumtype(
    request: Request,
    naam: str = Form(...),
    session: Session = Depends(get_session)
):
    new_jubileumtype = Jubileumtypes(naam=naam)
    session.add(new_jubileumtype)
    session.commit()
    return RedirectResponse(url="/jubileumtypes", status_code=303)

@router.get("/{jubileumtype_id}/edit", response_class=HTMLResponse, name="edit_jubileumtype")
async def edit_jubileumtype(request: Request, jubileumtype_id: int, session: Session = Depends(get_session)):
    jubileumtype = session.get(Jubileumtypes, jubileumtype_id)
    if not jubileumtype:
        raise HTTPException(status_code=404, detail="Jubileumtype niet gevonden")
    return templates.TemplateResponse("jubileumtype_form.html", {"request": request, "jubileumtype": jubileumtype})

@router.post("/{jubileumtype_id}/edit", response_class=HTMLResponse, name="update_jubileumtype")
async def update_jubileumtype(
    request: Request,
    jubileumtype_id: int,
    naam: str = Form(...),
    session: Session = Depends(get_session)
):
    jubileumtype = session.get(Jubileumtypes, jubileumtype_id)
    if not jubileumtype:
        raise HTTPException(status_code=404, detail="Jubileumtype niet gevonden")
    jubileumtype.naam = naam
    session.add(jubileumtype)
    session.commit()
    return RedirectResponse(url="/jubileumtypes", status_code=303)

@router.get("/{jubileumtype_id}/delete", response_class=HTMLResponse, name="delete_jubileumtype")
async def delete_jubileumtype(request: Request, jubileumtype_id: int, session: Session = Depends(get_session)):
    jubileumtype = session.get(Jubileumtypes, jubileumtype_id)
    if not jubileumtype:
        raise HTTPException(status_code=404, detail="Jubileumtype niet gevonden")
    session.delete(jubileumtype)
    session.commit()
    return RedirectResponse(url="/jubileumtypes", status_code=303)