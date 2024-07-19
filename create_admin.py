import click
from sqlmodel import Session, select
from app.database import engine
from app.models.models import Gebruikers, Rollen

@click.command()
@click.option('--email', prompt='Administrator email', help='Email van de nieuwe Administrator')
@click.option('--naam', prompt='Naam', help='Naam van de nieuwe Administrator')
@click.option('--google-id', prompt='Google ID', help='Google ID van de nieuwe Administrator')
def add_administrator(email: str, naam: str, google_id: str):
    with Session(engine) as session:
        # Controleer of de Administrator rol bestaat, maak aan indien nodig
        admin_role = session.exec(select(Rollen).where(Rollen.naam == "Administrator")).first()
        if not admin_role:
            admin_role = Rollen(naam="Administrator")
            session.add(admin_role)
            session.commit()

        # Controleer of de gebruiker al bestaat
        existing_user = session.exec(select(Gebruikers).where(Gebruikers.email == email)).first()
        if existing_user:
            click.echo(f"Gebruiker met email {email} bestaat al.")
            return

        # Maak de nieuwe Administrator aan
        new_admin = Gebruikers(
            email=email,
            naam=naam,
            google_id=google_id,
            rol_id=admin_role.id
        )
        session.add(new_admin)
        session.commit()
        click.echo(f"Administrator {naam} ({email}) is succesvol toegevoegd.")

if __name__ == '__main__':
    add_administrator()