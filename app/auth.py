from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from .logging_config import app_logger
from functools import wraps
from sqlmodel import Session, select
from .database import get_session
from .models.models import User
from datetime import datetime
import os

config = Config('.env')
oauth = OAuth(config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    },
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
)

router = APIRouter()

@router.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)
    
@router.get('/auth')
async def auth(request: Request, session: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    app_logger.debug(f"Received token: {token}")

    user_info = token.get('userinfo')
    if user_info:
        email = user_info['email']
        google_id = user_info['sub']
        app_logger.debug(f"User info from token: {user_info}")
        
        # Zoek de gebruiker in de database
        db_user = session.exec(select(User).where(User.email == email)).first()
        if db_user:
            app_logger.debug(f"User gevonden in database: {db_user}")
            # Update last_login en Google-ID
            db_user.last_login = datetime.utcnow()
            db_user.google_id = google_id
            session.add(db_user)
            session.commit()
        else:
            # Als de gebruiker niet bestaat, stuur ze naar een "niet geautoriseerd" pagina
            app_logger.debug(f"User NIET gevonden in database: {db_user}")
            return RedirectResponse(url='/not_authorized')
        
        # Sla relevante informatie op in de sessie
        request.session['user'] = {
            'id': db_user.id,
            'email': db_user.email,
            'name': db_user.name,
            'role': db_user.role,
            'google_id': db_user.google_id
        }
        app_logger.debug(f"Session after setting user: {request.session}")
        return RedirectResponse(url='/')
    else:
        raise HTTPException(status_code=400, detail="Kon gebruikersinformatie niet ophalen")
    

@router.get('/logout')
async def logout(request: Request):
    user = request.session.get('user')
    if user:
        app_logger.info(f"User logged out: {user.get('email', 'Unknown')}")
    request.session.pop('user', None)
    app_logger.debug(f"Session after logout: {request.session}")
    return RedirectResponse(url='/')

def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = request.session.get('user')
        if not user:
            raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
        return await func(request, *args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = request.session.get('user')
            if not user:
                raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
            if user.get('role')!= role:
                raise HTTPException(status_code=403, detail="Not authorized")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator