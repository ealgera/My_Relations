from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Families, Personen, Gebruikers
from ..auth import login_required, role_required, get_current_user, owner_or_admin_required
from ..logging_config import app_logger

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@login_required
async def list_families(request: Request, session: Session = Depends(get_session)):
    families = session.exec(select(Families)).all()
    return templates.TemplateResponse("families.html", {"request": request, "families": families})

@router.get("/search", response_class=HTMLResponse)
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def search_families(request: Request):
    return templates.TemplateResponse("family_form.html", {"request": request})

@router.get("/new", response_class=HTMLResponse)
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def new_family(request: Request):
    return templates.TemplateResponse("family_form.html", {"request": request})

@router.post("/new")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def new_family(
    request: Request,
    familienaam : str     = Form(...),
    straatnaam  : str     = Form(...),
    huisnummer  : str     = Form(...),
    huisnummer_toevoeging: str = Form(None),
    postcode    : str     = Form(...),
    plaats      : str     = Form(...),
    current_user: dict    = Depends(get_current_user),
    session     : Session = Depends(get_session)
):
    app_logger.debug(f"Create Family: {familienaam}, {straatnaam}, {huisnummer}, {huisnummer_toevoeging}, {postcode}, {plaats}")
    new_family = Families(familienaam=familienaam, straatnaam=straatnaam, huisnummer=huisnummer,
                          huisnummer_toevoeging=huisnummer_toevoeging, postcode=postcode, plaats=plaats,
                          created_by=current_user['id'])
    session.add(new_family)
    session.commit()
    return RedirectResponse(url="/families", status_code=303)

@router.get("/{family_id}/edit", response_class=HTMLResponse)
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def edit_family(request: Request, family_id: int, session: Session = Depends(get_session)):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    return templates.TemplateResponse("family_form.html", {"request": request, "family": family})

@router.post("/{family_id}/edit")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
@owner_or_admin_required(Families)
async def update_family(
    request: Request,
    family_id: int,
    familienaam: str = Form(...),
    straatnaam: str = Form(...),
    huisnummer: str = Form(...),
    huisnummer_toevoeging: str = Form(None),
    postcode: str = Form(...),
    plaats: str = Form(...),
    current_user: Gebruikers = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    if family.created_by != current_user['id']: # and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Geen toestemming om deze familie te bewerken")
    
    family.familienaam = familienaam
    family.straatnaam = straatnaam
    family.huisnummer = huisnummer
    family.huisnummer_toevoeging = huisnummer_toevoeging
    family.postcode = postcode
    family.plaats = plaats
    
    session.add(family)
    session.commit()
    return RedirectResponse(url="/families", status_code=303)

@router.get("/{family_id}/delete")
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
@owner_or_admin_required(Families)
async def delete_family(request: Request, family_id: int, session: Session = Depends(get_session)):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    session.delete(family)
    session.commit()
    return RedirectResponse(url="/families", status_code=303)

@router.get("/{family_id}", response_class=HTMLResponse)
@login_required
async def family_detail(request: Request, family_id: int, session: Session = Depends(get_session)):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    
    return templates.TemplateResponse("familie_detail.html", {
        "request": request, 
        "family": family,
        "members": family.personen
    })