from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Jubilea, Personen, Families, Gebruikers, Rollen
from ..auth import role_required
from ..logging_config import app_logger
import re
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path as PathLib  # Hernoem de import om verwarring te voorkomen met fastapi Path

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MODEL_MAP = {
    'jubilea': Jubilea,
    'personen': Personen,
    'families': Families,
}

@router.get("/users", response_class=HTMLResponse, name="admin_list_users")
@role_required("Administrator")
async def admin_list_users(request: Request, session: Session = Depends(get_session)):
    statement = select(Gebruikers, Rollen).join(Rollen)
    results = session.exec(statement).all()
    gebruikers = [{"gebruiker": gebruiker, "rol": rol} for gebruiker, rol in results]
    
    # Debug logging
    app_logger.debug(f"[Admin] Number of users fetched: {len(gebruikers)}")
    for user in gebruikers:
        app_logger.debug(f"[Admin] User: {user['gebruiker'].naam}, Role: {user['rol'].naam}")
    
    return templates.TemplateResponse("gebruikers.html", {"request": request, "gebruikers": gebruikers})

@router.get("/users/add", response_class=HTMLResponse, name="add_account_form")
@role_required("Administrator")
async def add_account_form(request: Request, session: Session = Depends(get_session)):
    rollen = session.exec(select(Rollen)).all()
    return templates.TemplateResponse("add_account.html", {"request": request, "rollen": rollen})

@router.post("/users/add", response_class=RedirectResponse, name="add_account")
@role_required("Administrator")
async def add_account(
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
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse, name="edit_account")
@role_required("Administrator")
async def edit_account_form(request: Request, user_id: int = Path(...), session: Session = Depends(get_session)):
    user = session.get(Gebruikers, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    rollen = session.exec(select(Rollen)).all()
    return templates.TemplateResponse("edit_account.html", {"request": request, "user": user, "rollen": rollen})

@router.post("/users/{user_id}/edit", response_class=RedirectResponse, name="update_account")
@role_required("Administrator")
async def update_account(
    request: Request,
    user_id: int,
    email: str = Form(...),
    naam: str = Form(...),
    rol_id: int = Form(...),
    google_id: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.get(Gebruikers, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    user.email = email
    user.naam = naam
    user.rol_id = rol_id
    user.google_id = google_id
    session.add(user)
    session.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/users/{user_id}/delete", response_class=RedirectResponse, name="delete_account")
@role_required("Administrator")
async def delete_account(request: Request, user_id: int = Path(...), session: Session = Depends(get_session)):
    user = session.get(Gebruikers, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    session.delete(user)
    session.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@router.get("/change-owner", response_class=HTMLResponse)
@role_required("Administrator")
async def change_owner(
    request: Request,
    model: str = Query(None),
    page: int = Query(1, ge=1),
    session: Session = Depends(get_session)
):
    items = []
    if model and model in MODEL_MAP:
        query = select(MODEL_MAP[model], Gebruikers).join(Gebruikers, MODEL_MAP[model].created_by == Gebruikers.id)
        items = session.exec(query.offset((page - 1) * 10).limit(10)).all()

    users = session.exec(select(Gebruikers)).all()
    print(f"Gebruikers: {users}, type: {type(users)}")
    
    return templates.TemplateResponse("change_owner.html", {
        "request": request,
        "models": MODEL_MAP.keys(),
        "selected_model": model,
        "items": items,
        "page": page,
        "users": users,
    })

@router.post("/change-owner", response_class=RedirectResponse)
@role_required("Administrator")
async def post_change_owner(
    request: Request,
    model: str = Form(...),
    item_id: int = Form(...),
    new_owner_id: int = Form(...),
    session: Session = Depends(get_session)
):
    if model not in MODEL_MAP:
        raise HTTPException(status_code=400, detail="Invalid model")

    item = session.get(MODEL_MAP[model], item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    new_owner = session.get(Gebruikers, new_owner_id)
    if not new_owner:
        raise HTTPException(status_code=404, detail="New owner not found")

    item.created_by = new_owner_id
    session.add(item)
    session.commit()

    return RedirectResponse(url=f"/admin/change-owner?model={model}", status_code=303)

@router.post("/add-account", response_class=RedirectResponse)
@role_required("Administrator")
async def add_account(
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
    return RedirectResponse(url="/admin/add-account", status_code=303)

base_path = PathLib(__file__).parent.parent.parent

@router.get("/logs", response_class=HTMLResponse, name="view_logs")
@role_required("Administrator")
async def view_logs(
    request: Request,
    page: int = Query(1, ge=1),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    log_level: Optional[str] = Query(None),
    items_per_page: int = Query(50, le=100),
    session: Session = Depends(get_session)
):
    log_file_path = base_path / 'logs' / 'app.log'
    log_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) (\w+) (.+)')
    
    log_entries = []
    first_date = None
    try:
        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                match = log_pattern.match(line)
                if match:
                    date_str, level, message = match.groups()
                    log_datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S,%f')
                    
                    if first_date is None:
                        first_date = log_datetime.date()
                    
                    if date_from and log_datetime.date() < datetime.strptime(date_from, '%Y-%m-%d').date():
                        continue
                    if date_to and log_datetime.date() > datetime.strptime(date_to, '%Y-%m-%d').date():
                        continue
                    if log_level and level.lower() != log_level.lower():
                        continue
                    
                    log_entries.append({
                        'date': log_datetime,
                        'level': level,
                        'message': message
                    })
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Log file not found at {log_file_path}")

    # If date_from or date_to are not provided, set default values
    if not date_from:
        date_from = first_date.strftime('%Y-%m-%d') if first_date else None
    if not date_to:
        date_to = date.today().strftime('%Y-%m-%d')

    total_items = len(log_entries)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    page = min(max(1, page), total_pages)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    
    paginated_entries = log_entries[start_index:end_index]

    return templates.TemplateResponse("log_viewer.html", {
        "request": request,
        "log_entries": paginated_entries,
        "page": page,
        "total_pages": total_pages,
        "date_from": date_from,
        "date_to": date_to,
        "log_level": log_level,
        "items_per_page": items_per_page
    })