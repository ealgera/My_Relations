from sqlmodel import Session, select
from app.database import engine
from app.models.models import Families, Personen, Jubilea, Relatietypes, Relaties

def insert_test_data():
    with Session(engine) as session:
        # Maak testdata aan voor Families
        familie1 = Families(familienaam="De Vries", straatnaam="Hoofdstraat", huisnummer="10", postcode="1234AB", plaats="Amsterdam")
        familie2 = Families(familienaam="Jansen", straatnaam="Kerkweg", huisnummer="5", postcode="5678CD", plaats="Rotterdam")
        session.add(familie1)
        session.add(familie2)
        
        # Maak testdata aan voor Jubilea
        jubileum1 = Jubilea(jubileumnaam="Huwelijk", jubileumdag="2000-05-15")
        jubileum2 = Jubilea(jubileumnaam="Verjaardag", jubileumdag="1990-03-21")
        session.add(jubileum1)
        session.add(jubileum2)
        
        # Maak testdata aan voor Relatietypes
        relatietype1 = Relatietypes(relatienaam="Echtgenoot")
        relatietype2 = Relatietypes(relatienaam="Kind")
        session.add(relatietype1)
        session.add(relatietype2)
        
        # Commit om ID's te genereren
        session.commit()
        
        # Maak testdata aan voor Personen
        persoon1 = Personen(voornaam="Jan", achternaam="De Vries", familieId=familie1.familieId, jubileumId=jubileum1.jubileumId)
        persoon2 = Personen(voornaam="Marie", achternaam="De Vries", familieId=familie1.familieId, jubileumId=jubileum1.jubileumId)
        persoon3 = Personen(voornaam="Piet", achternaam="De Vries", familieId=familie1.familieId, jubileumId=jubileum2.jubileumId)
        session.add(persoon1)
        session.add(persoon2)
        session.add(persoon3)
        
        # Commit om ID's te genereren
        session.commit()
        
        # Maak testdata aan voor Relaties
        relatie1 = Relaties(persoonid1=persoon1.persoonId, persoonid2=persoon2.persoonId, relatietypeId=relatietype1.relatietypeId)
        relatie2 = Relaties(persoonid1=persoon1.persoonId, persoonid2=persoon3.persoonId, relatietypeId=relatietype2.relatietypeId)
        relatie3 = Relaties(persoonid1=persoon2.persoonId, persoonid2=persoon3.persoonId, relatietypeId=relatietype2.relatietypeId)
        session.add(relatie1)
        session.add(relatie2)
        session.add(relatie3)
        
        session.commit()
        
    print("Testdata successfully inserted.")

def test_relations():
    with Session(engine) as session:
        # Test Familie-Persoon relatie
        familie = session.exec(select(Families).where(Families.familienaam == "De Vries")).first()
        print(f"Familie: {familie.familienaam}")
        for persoon in familie.personen:
            print(f"- {persoon.voornaam} {persoon.achternaam}")
        
        print("\n")
        
        # Test Persoon-Jubileum relatie
        persoon = session.exec(select(Personen).where(Personen.voornaam == "Jan")).first()
        print(f"Persoon: {persoon.voornaam} {persoon.achternaam}")
        print(f"Jubileum: {persoon.jubileum.jubileumnaam} op {persoon.jubileum.jubileumdag}")
        
        print("\n")
        
        # Test Relaties
        relaties = session.exec(select(Relaties).where(Relaties.persoonid1 == persoon.persoonId)).all()
        for relatie in relaties:
            andere_persoon = session.get(Personen, relatie.persoonid2)
            relatietype = session.get(Relatietypes, relatie.relatietypeId)
            print(f"{persoon.voornaam} is {relatietype.relatienaam} van {andere_persoon.voornaam}")

if __name__ == "__main__":
    insert_test_data()
    test_relations()