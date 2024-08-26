from fastapi import APIRouter, Depends, Request, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt

from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from .logging_config import app_logger
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

@router.get('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)
    
@router.get('/auth')
async def auth(request: Request, session: Session = Depends(get_session)):
    token = await oauth.google.authorize_access_token(request)
    app_logger.debug(f"[AUTH] Received token: {token}")

    user_info = token.get('userinfo')
    if user_info:
        email = user_info['email']
        google_id = user_info['sub']
        app_logger.debug(f"User info from token: {user_info}")
        
        # Zoek de gebruiker in de database
        db_user = session.exec(select(Gebruikers).where(Gebruikers.email == email)).first()
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
            'name': db_user.naam,
            'role': db_user.rol.naam,
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
        print(f"\nLogin Required")
        print(f"Decorator args: {args}")
        print(f"Decorator kwargs: {kwargs}")
        app_logger.debug(f"Login Required - User in session: {user}")
        if not user:
            app_logger.debug(f"Login Required - No User found in session")
            raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
        return await func(request, *args, **kwargs)
    return wrapper

def role_required(allowed_roles: Union[str, List[str]]):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            user = request.session.get('user')
            app_logger.debug(f"Role Required - User in session: {user}")
            if not user:
                app_logger.debug(f"Role Required - No User found in session")
                raise HTTPException(status_code=303, detail="Not authenticated", headers={"Location": "/login"})
            
            user_role = user.get('role')
            
            if isinstance(allowed_roles, str):
                allowed_roles_list = [allowed_roles]
            else:
                allowed_roles_list = allowed_roles
            
            if user_role not in allowed_roles_list:
                response = RedirectResponse(url="/", status_code=302)
                response.set_cookie(key="auth_error", value="Je bent niet geautoriseerd voor deze actie", max_age=30)
                return response
            
            app_logger.debug(f"Role Required - Role is correct!")
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