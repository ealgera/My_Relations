from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Gebruikers, Rollen
from ..auth import login_required, role_required
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@login_required
@role_required("Administrator")
async def list_users(request: Request, session: Session = Depends(get_session)):
    users = session.exec(select(Gebruikers)).all()
    return templates.TemplateResponse("gebruikers.html", {"request": request, "users": users})

@router.get("/new", response_class=HTMLResponse)
@login_required
@role_required("Administrator")
async def new_user(request: Request, session: Session = Depends(get_session)):
    rollen = session.exec(select(Rollen)).all()
    return templates.TemplateResponse("gebruikers_form.html", {
        "request": request,
        "rollen": rollen,
        "gebruiker": None  # Expliciet aangeven dat er geen bestaande gebruiker is
    })

@router.post("/new")
@login_required
@role_required("Administrator")
async def create_user(
    request: Request,
    email: str = Form(...),
    naam: str = Form(...),
    rol_id: int = Form(...),
    google_id: str = Form(...),
    session: Session = Depends(get_session)
):
    new_user = Gebruikers(email=email, naam=naam, rol_id=rol_id, google_id=google_id)
    session.add(new_user)
    session.commit()
    return RedirectResponse(url="/users", status_code=303)

@router.get("/{user_id}/edit", response_class=HTMLResponse)
@login_required
@role_required("Administrator")
async def edit_user(request: Request, user_id: int, session: Session = Depends(get_session)):
    user = session.get(Gebruikers, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    rollen = session.exec(select(Rollen)).all()
    if not rollen:
        raise HTTPException(status_code=404, detail="Rollen niet gevonden")

    return templates.TemplateResponse("gebruikers_form.html", {
        "request"  : request,
        "gebruiker": user,
        "rollen"   : rollen})

@router.post("/{user_id}/edit")
@login_required
@role_required("Administrator")
async def update_user(
    request: Request,
    user_id: int,
    email: str = Form(...),
    name: str = Form(...),
    role: str = Form(...),
    google_id: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.get(Gebruikers, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    user.email = email
    user.name = name
    user.role = role
    user.google_id = google_id
    session.add(user)
    session.commit()
    return RedirectResponse(url="/users", status_code=303)

@router.get("/{user_id}/delete")
@login_required
@role_required("Administrator")
async def delete_user(request: Request, user_id: int, session: Session = Depends(get_session)):
    user = session.get(Gebruikers, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    session.delete(user)
    session.commit()
    return RedirectResponse(url="/users", status_code=303)
