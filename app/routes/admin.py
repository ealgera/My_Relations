from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from ..database import get_session
from ..models.models import Jubilea, Personen, Families, Gebruikers  # Voeg andere modellen toe indien nodig
from ..auth import role_required

router = APIRouter()
templates = Jinja2Templates(directory="templates")

MODEL_MAP = {
    'jubilea': Jubilea,
    'personen': Personen,
    'families': Families,
}

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
