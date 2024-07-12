from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Families

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_families(request: Request, session: Session = Depends(get_session)):
    families = session.exec(select(Families)).all()
    return templates.TemplateResponse("families.html", {"request": request, "families": families})

@router.get("/new", response_class=HTMLResponse)
async def new_family(request: Request):
    return templates.TemplateResponse("family_form.html", {"request": request})

@router.post("/new")
async def create_family(
    request: Request,
    familienaam: str = Form(...),
    straatnaam: str = Form(...),
    huisnummer: str = Form(...),
    huisnummer_toevoeging: str = Form(None),
    postcode: str = Form(...),
    plaats: str = Form(...),
    session: Session = Depends(get_session)
):
    new_family = Families(familienaam=familienaam, straatnaam=straatnaam, huisnummer=huisnummer,
                          huisnummer_toevoeging=huisnummer_toevoeging, postcode=postcode, plaats=plaats)
    session.add(new_family)
    session.commit()
    return RedirectResponse(url="/families", status_code=303)

@router.get("/{family_id}/edit", response_class=HTMLResponse)
async def edit_family(family_id: int, request: Request, session: Session = Depends(get_session)):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    return templates.TemplateResponse("family_form.html", {"request": request, "family": family})

@router.post("/{family_id}/edit")
async def update_family(
    family_id: int,
    familienaam: str = Form(...),
    straatnaam: str = Form(...),
    huisnummer: str = Form(...),
    huisnummer_toevoeging: str = Form(None),
    postcode: str = Form(...),
    plaats: str = Form(...),
    session: Session = Depends(get_session)
):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    
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
async def delete_family(family_id: int, session: Session = Depends(get_session)):
    family = session.get(Families, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="Familie niet gevonden")
    session.delete(family)
    session.commit()
    return RedirectResponse(url="/families", status_code=303)