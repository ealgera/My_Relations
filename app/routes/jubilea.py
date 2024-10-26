from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func, or_
from ..database import get_session
from ..models.models import Jubilea, Personen, Jubileumtypes
from datetime import datetime
from typing import Optional
from ..auth import login_required, role_required, get_current_user, owner_or_admin_required
from ..logging_config import app_logger, log_debug, log_error
from config import get_settings
from PIL import Image
import os

router = APIRouter()

templates = Jinja2Templates(directory="templates")
settings  = get_settings()

def process_photo(file: UploadFile, jubileum_id: int):
    log_debug(f"[Jubilea - Process_photo] started...")
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"jubileum_{jubileum_id}{file_extension}"
    filepath = settings.FOTO_DIR / filename
    
    log_debug(f"[Jubilea - Process_photo] Probeer foto te bewaren: {filepath}")
    
    try:
        with Image.open(file.file) as img:
            img.thumbnail((1024, 1024))
            img.save(filepath, optimize=True, quality=85)
            log_debug(f"[Jubilea - Process_photo] Foto successvol bewaard!")
        
    except Exception as e:
        log_error(f"[Jubilea - Process_photo] Fout tijdens het bewaren: {str(e)}")
        raise
    
    log_debug(f"[Jubilea - Process_photo] Foto Returning URL: /fotos/{filename}")
    return f"/fotos/{filename}"

@router.post("/search", response_class=HTMLResponse)
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def search_jubilea(request: Request, search_term: str = Form(None), session: Session = Depends(get_session)):
    log_debug(f"[Jubilea - Zoeken]: {search_term}")

    query = select(Jubilea, Personen, Jubileumtypes).outerjoin(Personen).join(Jubileumtypes)
    if search_term:
        query = query.where(
            or_(
                Personen.voornaam.ilike(f"%{search_term}%"),
                Personen.achternaam.ilike(f"%{search_term}%"),
                Jubilea.omschrijving.ilike(f"%{search_term}%"),
                Jubilea.jubileumnaam.ilike(f"%{search_term}%"),
                Jubileumtypes.naam.ilike(f"%{search_term}%")
            )
        )

    results = session.exec(query).all()

    jubilea = [
        {
            "id": jubileum.id,
            "jubileumdag": jubileum.jubileumdag,
            "omschrijving": jubileum.omschrijving,
            "jubileumnaam": jubileum.jubileumnaam,
            "url": jubileum.url,
            "jubileumtype": jubileumtype.naam,
            "persoon": f"{persoon.voornaam} {persoon.achternaam}" if persoon else None
        }
        for jubileum, persoon, jubileumtype in results
    ]

    return templates.TemplateResponse("jubilea.html", {"request": request, "jubilea": jubilea})

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
            "jubileumnaam": jubileum.jubileumnaam,
            "url": jubileum.url,
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
    jubileumnaam   : str     = Form(...),
    omschrijving   : str     = Form(None),
    url            : str     = Form(None),
    persoon_id     : Optional[int] = Form(None),
    foto           : UploadFile    = File(None),
    current_user   : dict    = Depends(get_current_user),
    session        : Session = Depends(get_session)
):
    jubileumdag = datetime.strptime(jubileumdag, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    new_jubileum = Jubilea(
        jubileumtype_id=jubileumtype_id,
        jubileumdag=jubileumdag,
        jubileumnaam=jubileumnaam,
        omschrijving=omschrijving,
        url=url,
        persoon_id=persoon_id,
        created_by=current_user['id']
    )
    session.add(new_jubileum)
    session.commit()
    session.refresh(new_jubileum)

    if foto and foto.filename:
        foto_url = process_photo(foto, new_jubileum.id)
        new_jubileum.foto_url = foto_url
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

    formatted_date = datetime.strptime(jubileum.jubileumdag, "%Y-%m-%d").strftime("%Y-%m-%d")
    
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
@owner_or_admin_required(Jubilea)
async def update_jubileum(
    request: Request,
    jubileum_id    : int,
    action         : str     = Form(...),
    jubileumtype_id: int     = Form(None),
    jubileumdag    : str     = Form(None),
    jubileumnaam   : str     = Form(None),
    omschrijving   : str     = Form(None),
    url            : str     = Form(None),
    persoon_id     : Optional[int] = Form(None),
    foto           : UploadFile    = File(None),
    session        : Session = Depends(get_session)
):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")

    if action == "delete_photo":
        if jubileum.foto_url:
            foto_path = settings.FOTO_DIR / jubileum.foto_url.split('/')[-1]
            if foto_path.exists():
                os.remove(foto_path)
            jubileum.foto_url = None
            session.commit()
        return RedirectResponse(url=f"/jubilea/{jubileum_id}/edit", status_code=303)

    elif action == "update_jubileum":
        jubileumdag = datetime.strptime(jubileumdag, "%Y-%m-%d").strftime("%Y-%m-%d")
        
        jubileum.jubileumtype_id = jubileumtype_id
        jubileum.jubileumdag     = jubileumdag
        jubileum.jubileumnaam    = jubileumnaam
        jubileum.omschrijving    = omschrijving
        jubileum.url             = url
        jubileum.persoon_id      = persoon_id

        if foto and foto.filename:
            foto_url = process_photo(foto, jubileum.id)
            log_debug(f"Foto voor Jubileum {foto_url} - {jubileum.id} aangepast")
            jubileum.foto_url = foto_url
        
        session.add(jubileum)
        session.commit()
        return RedirectResponse(url="/jubilea", status_code=303)

    else:
        raise HTTPException(status_code=400, detail="Ongeldige actie")

@router.get("/{jubileum_id}/delete", name="delete_jubileum")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
@owner_or_admin_required(Jubilea)
async def delete_jubileum(request: Request, jubileum_id: int, session: Session = Depends(get_session)):
    jubileum = session.get(Jubilea, jubileum_id)
    if not jubileum:
        raise HTTPException(status_code=404, detail="Jubileum niet gevonden")
    session.delete(jubileum)
    session.commit()
    return RedirectResponse(url="/jubilea", status_code=303)
