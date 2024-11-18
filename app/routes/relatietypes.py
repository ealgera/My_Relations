from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Relatietypes

router = APIRouter()

templates = Jinja2Templates(directory="templates")

@router.get("/", name="list_relatietypes")
async def list_relatietypes(request: Request, session: Session = Depends(get_session)):
    relatietypes = session.exec(select(Relatietypes)).all()
    return templates.TemplateResponse("relatietypes.html", {"request": request, "relatietypes": relatietypes})

@router.get("/new", name="new_relatietype")
async def new_relatietype(request: Request):
    return templates.TemplateResponse("relatietype_form.html", {"request": request})

@router.post("/new", name="create_relatietype")
async def create_relatietype(
    request: Request,
    relatienaam: str = Form(...),
    symmetrisch: bool = Form(False),
    session: Session = Depends(get_session)
):
    new_relatietype = Relatietypes(relatienaam=relatienaam, symmetrisch=symmetrisch)
    session.add(new_relatietype)
    session.commit()
    return RedirectResponse(url="/relatietypes", status_code=303)

@router.get("/{relatietype_id}/edit", name="edit_relatietype")
async def edit_relatietype(relatietype_id: int, request: Request, session: Session = Depends(get_session)):
    relatietype = session.get(Relatietypes, relatietype_id)
    if not relatietype:
        raise HTTPException(status_code=404, detail="Relatietype niet gevonden")
    return templates.TemplateResponse("relatietype_form.html", {"request": request, "relatietype": relatietype})

@router.post("/{relatietype_id}/edit", name="update_relatietype")
async def update_relatietype(
    relatietype_id: int,
    relatienaam: str = Form(...),
    symmetrisch: bool = Form(False),
    session: Session = Depends(get_session)
):
    relatietype = session.get(Relatietypes, relatietype_id)
    if not relatietype:
        raise HTTPException(status_code=404, detail="Relatietype niet gevonden")
    
    relatietype.relatienaam = relatienaam
    relatietype.symmetrisch = symmetrisch
    session.add(relatietype)
    session.commit()
    return RedirectResponse(url="/relatietypes", status_code=303)

@router.get("/{relatietype_id}/delete", name="delete_relatietype")
async def delete_relatietype(relatietype_id: int, session: Session = Depends(get_session)):
    relatietype = session.get(Relatietypes, relatietype_id)
    if not relatietype:
        raise HTTPException(status_code=404, detail="Relatietype niet gevonden")
    session.delete(relatietype)
    session.commit()
    return RedirectResponse(url="/relatietypes", status_code=303)
