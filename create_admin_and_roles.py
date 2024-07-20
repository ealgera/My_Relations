import click
from sqlmodel import Session, select
from app.database import engine
from app.models.models import Gebruikers, Rollen

def init_roles(session):
    roles = ["Administrator", "Beheerder", "Gebruiker"]
    for role_name in roles:
        existing_role = session.exec(select(Rollen).where(Rollen.naam == role_name)).first()
        if not existing_role:
            new_role = Rollen(naam=role_name)
            session.add(new_role)
            print(f"Rol '{role_name}' aangemaakt.")
        else:
            print(f"Rol '{role_name}' bestaat al.")
    session.commit()

@click.command()
@click.option('--email', prompt='Administrator email', help='Email van de nieuwe Administrator')
@click.option('--naam', prompt='Naam', help='Naam van de nieuwe Administrator')
@click.option('--google_id', prompt='Google ID', help='Google ID van de nieuwe Administrator')
def create_admin_and_roles(email: str, naam: str, google_id: str):
    with Session(engine) as session:
        print("Initialiseren van rollen...")
        init_roles(session)

        print("Controleren op bestaande gebruiker...")
        existing_user = session.exec(select(Gebruikers).where(Gebruikers.email == email)).first()
        if existing_user:
            print(f"Gebruiker met email {email} bestaat al.")
            return

        print("Ophalen van Administrator rol...")
        admin_role = session.exec(select(Rollen).where(Rollen.naam == "Administrator")).first()
        if not admin_role:
            print("Administrator rol niet gevonden. Er is iets misgegaan bij het initialiseren van de rollen.")
            return

        print("Aanmaken van nieuwe Administrator...")
        new_admin = Gebruikers(
            email=email,
            naam=naam,
            google_id=google_id,
            rol_id=admin_role.id
        )
        session.add(new_admin)
        session.commit()
        print(f"Administrator {naam} ({email}) is succesvol toegevoegd met de Administrator rol.")

if __name__ == '__main__':
    create_admin_and_roles()