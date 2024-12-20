from fastapi import APIRouter, Depends, Request, HTTPException, status
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from .logging_config import app_logger, log_info, log_debug
from functools import wraps
from sqlmodel import Session, select
from .database import get_session
from .models.models import Gebruikers
from datetime import datetime
from config import get_settings
from typing import List, Union

settings = get_settings()

oauth = OAuth()

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'
    },
    client_id     = settings.GOOGLE_CLIENT_ID, #  os.getenv('GOOGLE_CLIENT_ID'),
    client_secret = settings.GOOGLE_CLIENT_SECRET
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)
    
@router.get('/auth')
async def auth(request: Request, session: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    log_debug(f"[Auth] Received token: {token}")

    user_info = token.get('userinfo')
    if user_info:
        email = user_info['email']
        google_id = user_info['sub']
        log_debug(f"[Auth] User info from token: {user_info}")
        
        db_user = session.exec(select(Gebruikers).where(Gebruikers.email == email)).first()  # Zoek de gebruiker in de database
        if db_user:
            app_logger.debug(f"[Auth] User gevonden in database: {db_user}")
            db_user.last_login = datetime.utcnow()  # Update last_login en Google-ID
            db_user.google_id = google_id
            session.add(db_user)
            session.commit()
            
            request.session['user'] = {    # Sla relevante informatie op in de sessie
                'id': db_user.id,
                'email': db_user.email,
                'name': db_user.naam,
                'role': db_user.rol.naam,
                'google_id': db_user.google_id
            }
            app_logger.debug(f"[Auth] User logged in: {request.session['user'].get('email', 'Unknown')}")
            app_logger.debug(f"[Auth] Session after setting user: {request.session}")
            return RedirectResponse(url='/home', status_code=303)

        else:
            # Als de gebruiker niet bestaat, stuur ze naar een "niet geautoriseerd" pagina
            app_logger.debug(f"User NIET gevonden in database: {db_user}")
            return RedirectResponse(url=f'/?error=not_authorized&email={email}', status_code=303)
        
    else:
        raise HTTPException(status_code=400, detail="Kon gebruikersinformatie niet ophalen")    

@router.get('/logout')
async def logout(request: Request):
    log_debug(f"[AUTH] handling logout...")
    user = request.session.get('user')
    if user:
        app_logger.info(f"User logged out: {user.get('email', 'Unknown')}")
    request.session.pop('user', None)
    log_debug(f"[AUTH] Session after logout: {request.session}")
    return RedirectResponse(url='/')

def login_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if request is None:
            for arg in kwargs.values():
                if isinstance(arg, Request):
                    request = arg
                    break
        
        if request is None:
            raise HTTPException(status_code=500, detail="Request object not found")
            
        log_debug(f"[AUTH] Login required - Checking login for route: {request.url.path}")
        if 'user' not in request.session:
            log_debug("[AUTH] Login Required - No User found in session, redirecting to login")
            raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
        
        return await func(*args, **kwargs)
    return wrapper

def role_required(allowed_roles: Union[str, List[str]]):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            log_debug(f"[AUTH] Role required - Checking role for route: {request.url.path}")
            user = request.session.get('user')
            log_debug(f"[AUTH] Role Required - User in session: {user}")
            if not user:
                log_debug(f"[AUTH] Role Required - No User found in session")
                raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
            
            user_role = user.get('role')
            
            if isinstance(allowed_roles, str):
                allowed_roles_list = [allowed_roles]
            else:
                allowed_roles_list = allowed_roles
            
            if user_role not in allowed_roles_list:
                log_debug(f"[AUTH] Role Required - Role is not allowed...")
                response = RedirectResponse(url="/", status_code=302)
                response.set_cookie(key="auth_error", value="Je bent niet geautoriseerd voor deze actie", max_age=30)
                return response
            
            log_debug(f"[AUTH] Role Required - Role is allowed!")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_current_user(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def owner_or_admin_required(model):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            current_user = get_current_user(request)
            session = next(get_session())
            
            id_param = next((value for key, value in kwargs.items() if key.endswith('_id')), None)
            if id_param is None:
                raise HTTPException(status_code=400, detail="Er is een probleem opgetreden bij het identificeren van het record.")
            
            item = session.get(model, id_param)
            
            if not item:
                raise HTTPException(status_code=404, detail=f"Het gevraagde {model.__name__.lower()} record kon niet worden gevonden.")
            
            if item.created_by != current_user['id'] and current_user['role'] != "Administrator":
                raise HTTPException(
                    status_code=403, 
                    detail=f"U heeft geen toestemming om dit {model.__name__.lower()} record te bewerken. "
                           f"Alleen de maker van het record of een administrator kan wijzigingen aanbrengen."
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
