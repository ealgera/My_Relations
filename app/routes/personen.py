from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Personen, Families, Gebruikers
from ..auth import login_required, role_required, get_current_user, owner_or_admin_required
from ..logging_config import log_info, log_debug, log_error
from datetime import datetime
from config import get_settings
from PIL import Image
import os
# from pathlib import Path

router    = APIRouter()

templates = Jinja2Templates(directory="templates")
settings  = get_settings()

def process_photo(file: UploadFile, person_id: int):
    log_debug(f"[Process_photo] started...")
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"person_{person_id}{file_extension}"
    filepath = settings.FOTO_DIR / filename
    
    log_debug(f"[Process_photo] Attempting to save file: {filepath}")
    
    try:
        with Image.open(file.file) as img:
            # log_debug(f"[Process_photo] Image opened successfully")
            img.thumbnail((300, 300))
            # log_debug(f"[Process_photo] Image resized")
            img.save(filepath, optimize=True, quality=85)
            log_debug(f"[Process_photo] Image saved successfully")
        
        # Extra controles
        # if os.path.exists(filepath):
        #     log_debug(f"[Process_photo] File exists at {filepath}")
        #     log_debug(f"[Process_photo] File size: {os.path.getsize(filepath)} bytes")
        # else:
        #     log_error(f"[Process_photo] File does not exist at {filepath}")
            
        # Controleer de inhoud van de directory
        # log_debug(f"[Process_photo] Contents of {settings.FOTO_DIR}:")
        # for item in os.listdir(settings.FOTO_DIR):
        #     log_debug(f"  - {item}")
    
    except Exception as e:
        log_error(f"[Process_photo] Error saving image: {str(e)}")
        raise
    
    log_debug(f"[Process_photo] Returning URL: /fotos/{filename}")
    return f"/fotos/{filename}"

@router.get("/", response_class=HTMLResponse)
@login_required
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
    voornaam    : str        = Form(...),
    achternaam  : str        = Form(...),
    familie_id  : int        = Form(...),
    leeft       : bool       = Form(False),
    foto        : UploadFile = File(None),
    current_user: dict       = Depends(get_current_user),
    session     : Session    = Depends(get_session)):

    new_persoon = Personen(voornaam=voornaam, achternaam=achternaam, familie_id=familie_id,
        leeft=leeft,created_by=current_user['id'])
    session.add(new_persoon)
    session.commit()
    session.refresh(new_persoon)

    if foto and foto.filename:
        foto_url = process_photo(foto, new_persoon.id)
        new_persoon.foto_url = foto_url
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
    request     : Request,
    persoon_id  : int,
    voornaam    : str        = Form(...),
    achternaam  : str        = Form(...),
    familie_id  : int        = Form(...),
    leeft       : bool       = Form(False),
    foto        : UploadFile = File(None),
    current_user: Gebruikers = Depends(get_current_user),
    session     : Session    = Depends(get_session)
):
    form_data = await request.form()
    log_debug(f"[Update_Persoon] Request form data: {form_data}")
    log_debug(f"[Update_Persoon] Foto info: filename={foto.filename if foto else 'None'}, content_type={foto.content_type if foto else 'None'}")
    
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    # if persoon.created_by != current_user['id']: # and current_user.role != "admin":
        # raise HTTPException(status_code=403, detail="Geen toestemming om deze familie te bewerken")

    # session.refresh(persoon)

    persoon.voornaam   = voornaam
    persoon.achternaam = achternaam
    persoon.familie_id = familie_id
    persoon.leeft      = leeft

    if foto and foto.filename:
        foto_url = process_photo(foto, persoon.id)
        log_debug(f"[Update_Persoon] Foto voor persoon {foto_url} - {persoon.id} aangepast")

        persoon.foto_url = foto_url

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

@router.get("/{persoon_id}", response_class=HTMLResponse)
@login_required
async def persoon_detail(request: Request, persoon_id: int, session: Session = Depends(get_session)):
    persoon = session.get(Personen, persoon_id)
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    
    # Combineer relaties waarin de persoon persoon1 of persoon2 is
    alle_relaties = persoon.relaties_als_persoon1 + persoon.relaties_als_persoon2
    
    # Bereid de relatie-informatie voor
    relaties_info = []
    for relatie in alle_relaties:
        gerelateerde_persoon = relatie.persoon2 if relatie.persoon1_id == persoon_id else relatie.persoon1
        relaties_info.append({
            "relatietype": relatie.relatietype,
            "gerelateerde_persoon": gerelateerde_persoon
        })
    
    # Haal jubilea op
    jubilea = persoon.jubilea
    
    return templates.TemplateResponse("persoon_detail.html", {
        "request": request,
        "persoon": persoon,
        "relaties": relaties_info,
        "jubilea": jubilea
    })

@router.post("/{persoon_id}/delete_photo", name="delete_person_photo")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def delete_person_photo(request: Request, persoon_id: int, session: Session = Depends(get_session)):
    persoon = session.get(Personen, persoon_id)
    log_debug(f"[Personen] - *** Verwijder foto bij {persoon.voornaam}, {persoon.achternaam} ***")
    if not persoon:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    
    if persoon.foto_url:  # Verwijder de foto van het bestandssysteem
        foto_path = settings.FOTO_DIR / persoon.foto_url.split('/')[-1]
        log_debug(f"Pad naar foto: {foto_path}")
        if foto_path.exists():
            log_debug(f"Pad naar foto bestaaat!")
            os.remove(foto_path)
        
        persoon.foto_url = None  # Verwijder de foto URL ook uit de database
        session.commit()
    
    return RedirectResponse(url=f"/personen/{persoon_id}/edit", status_code=303)