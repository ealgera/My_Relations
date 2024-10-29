from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, or_
from sqlalchemy.orm import aliased
from ..database import get_session
from ..models.models import Relaties, Personen, Relatietypes
from ..auth import login_required, role_required, get_current_user

from ..logging_config import app_logger

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.post("/search", response_class=HTMLResponse)
@login_required
@role_required(["Administrator", "Beheerder", "Gebruiker"])
async def search_relaties(request: Request, search_term: str = Form(None), session: Session = Depends(get_session)):
    app_logger.debug(f"[Relaties - Zoeken]: {search_term}")

    Persoon1 = aliased(Personen)
    Persoon2 = aliased(Personen)

    query = select(
        Relaties.id,
        Relaties.persoon1_id,
        Relaties.persoon2_id,
        Relaties.relatietype_id,
        Persoon1.voornaam.label('persoon1_voornaam'),
        Persoon1.achternaam.label('persoon1_achternaam'),
        Relatietypes.relatienaam,
        Persoon2.voornaam.label('persoon2_voornaam'),
        Persoon2.achternaam.label('persoon2_achternaam')
    ).join(
        Persoon1, Relaties.persoon1_id == Persoon1.id
    ).join(
        Relatietypes, Relaties.relatietype_id == Relatietypes.id
    ).outerjoin(
        Persoon2, Relaties.persoon2_id == Persoon2.id
    )

    if search_term:
        query = query.where(
            or_(
                Persoon1.voornaam.ilike(f"%{search_term}%"),
                Persoon1.achternaam.ilike(f"%{search_term}%"),
                Persoon2.voornaam.ilike(f"%{search_term}%"),
                Persoon2.achternaam.ilike(f"%{search_term}%"),
                Relatietypes.relatienaam.ilike(f"%{search_term}%")
            )
        )

    results = session.exec(query).all()
    
    relaties = []
    for row in results:
        relaties.append({
            "id": row.id,
            "persoon1": {
                "id": row.persoon1_id,
                "voornaam": row.persoon1_voornaam,
                "achternaam": row.persoon1_achternaam
            },
            "persoon2": {
                "id": row.persoon2_id,
                "voornaam": row.persoon2_voornaam,
                "achternaam": row.persoon2_achternaam
            },
            "relatietype": {
                "id": row.relatietype_id,
                "relatienaam": row.relatienaam
            }
        })

    return templates.TemplateResponse("relaties.html", {"request": request, "relaties": relaties})

@router.get("/", response_class=HTMLResponse)
@login_required
async def list_relaties(request: Request, session: Session = Depends(get_session)):
    app_logger.debug("list_relaties functie is aangeroepen")
    Persoon1 = aliased(Personen)
    Persoon2 = aliased(Personen)

    query = select(
        Relaties.id,
        Relaties.persoon1_id,
        Relaties.persoon2_id,
        Relaties.relatietype_id,
        Persoon1.voornaam.label('persoon1_voornaam'),
        Persoon1.achternaam.label('persoon1_achternaam'),
        Relatietypes.relatienaam,
        Persoon2.voornaam.label('persoon2_voornaam'),
        Persoon2.achternaam.label('persoon2_achternaam')
    ).join(
        Persoon1, Relaties.persoon1_id == Persoon1.id
    ).join(
        Relatietypes, Relaties.relatietype_id == Relatietypes.id
    ).outerjoin(
        Persoon2, Relaties.persoon2_id == Persoon2.id
    )

    # Log de SQL query
    sql = query.compile(compile_kwargs={"literal_binds": True})
    app_logger.debug(f"List Relaties: Generated SQL query: {sql}")
    
    results = session.exec(query).all()
    
    relaties = []
    for row in results:
        relaties.append({
            "id": row.id,
            "persoon1": {
                "id": row.persoon1_id,
                "voornaam": row.persoon1_voornaam,
                "achternaam": row.persoon1_achternaam
            },
            "persoon2": {
                "id": row.persoon2_id,
                "voornaam": row.persoon2_voornaam,
                "achternaam": row.persoon2_achternaam
            },
            "relatietype": {
                "id": row.relatietype_id,
                "relatienaam": row.relatienaam
            }
        })
    
    return templates.TemplateResponse("relaties.html", {"request": request, "relaties": relaties})

@router.get("/new", response_class=HTMLResponse)
@login_required
async def new_relatie(request: Request, session: Session = Depends(get_session)):
    personen = session.exec(select(Personen)).all()
    relatietypes = session.exec(select(Relatietypes)).all()
    return templates.TemplateResponse("relaties_form.html", {"request": request, "personen": personen, "relatietypes": relatietypes})

@router.post("/new")
@login_required
async def create_relatie(
    request: Request,
    persoon1_id: int = Form(...),
    persoon2_id: int = Form(...),
    relatietype_id: int = Form(...),
    session: Session = Depends(get_session)
):
    if persoon1_id == persoon2_id:
        raise HTTPException(status_code=400, detail="Een persoon kan geen relatie met zichzelf hebben")
    new_relatie = Relaties(persoon1_id=persoon1_id, persoon2_id=persoon2_id, relatietype_id=relatietype_id)
    session.add(new_relatie)
    session.commit()
    return RedirectResponse(url="/relaties", status_code=303)

@router.get("/{relatie_id}/edit", response_class=HTMLResponse)
@login_required
async def edit_relatie(relatie_id: int, request: Request, session: Session = Depends(get_session)):
    relatie = session.get(Relaties, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    personen = session.exec(select(Personen)).all()
    relatietypes = session.exec(select(Relatietypes)).all()
    return templates.TemplateResponse("relaties_form.html", {"request": request, "relatie": relatie, "personen": personen, "relatietypes": relatietypes})

@router.post("/{relatie_id}/edit")
@login_required
async def update_relatie(
    relatie_id: int,
    persoon1_id: int = Form(...),
    persoon2_id: int = Form(...),
    relatietype_id: int = Form(...),
    session: Session = Depends(get_session)
):
    relatie = session.get(Relaties, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    
    relatie.persoon1_id = persoon1_id
    relatie.persoon2_id = persoon2_id
    relatie.relatietype_id = relatietype_id

    if persoon1_id == persoon2_id:
        raise HTTPException(status_code=400, detail="Een persoon kan geen relatie met zichzelf hebben")
    
    session.add(relatie)
    session.commit()
    return RedirectResponse(url="/relaties", status_code=303)

@router.get("/{relatie_id}/delete")
@login_required
async def delete_relatie(relatie_id: int, session: Session = Depends(get_session)):
    relatie = session.get(Relaties, relatie_id)
    if not relatie:
        raise HTTPException(status_code=404, detail="Relatie niet gevonden")
    session.delete(relatie)
    session.commit()
    return RedirectResponse(url="/relaties", status_code=303)
