import os
import unittest
from sqlmodel import Session, select

# Zet de omgeving op 'testing' voordat we iets importeren
os.environ['TESTING'] = 'True'

# Nu importeren we de database configuratie
from app.database import engine, create_db_and_tables
from app.models.models import Families, Personen, Jubilea, Relatietypes, Relaties

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Controleer of we daadwerkelijk de testdatabase gebruiken
        assert 'test.db' in str(engine.url), "Not using test database!"
        # Maak de testdatabase en tabellen aan
        create_db_and_tables()

    def setUp(self):
        # Setup test data
        self.session = Session(engine)
        self.insert_test_data()

    def tearDown(self):
        # Clean up after each test
        self.session.close()

    def insert_test_data(self):
        # Insert test data similar to your test_relations.py
        familie1 = Families(familienaam="De Vries", straatnaam="Hoofdstraat", huisnummer="10", postcode="1234AB", plaats="Amsterdam")
        familie2 = Families(familienaam="Jansen", straatnaam="Kerkweg", huisnummer="5", postcode="5678CD", plaats="Rotterdam")
        self.session.add(familie1)
        self.session.add(familie2)
        
        jubileum1 = Jubilea(jubileumnaam="Huwelijk", jubileumdag="2000-05-15")
        jubileum2 = Jubilea(jubileumnaam="Verjaardag", jubileumdag="1990-03-21")
        self.session.add(jubileum1)
        self.session.add(jubileum2)
        
        relatietype1 = Relatietypes(relatienaam="Echtgenoot")
        relatietype2 = Relatietypes(relatienaam="Kind")
        self.session.add(relatietype1)
        self.session.add(relatietype2)
        
        self.session.commit()
        
        persoon1 = Personen(voornaam="Jan", achternaam="De Vries", familieId=familie1.familieId, jubileumId=jubileum1.jubileumId)
        persoon2 = Personen(voornaam="Marie", achternaam="De Vries", familieId=familie1.familieId, jubileumId=jubileum1.jubileumId)
        persoon3 = Personen(voornaam="Piet", achternaam="De Vries", familieId=familie1.familieId, jubileumId=jubileum2.jubileumId)
        self.session.add(persoon1)
        self.session.add(persoon2)
        self.session.add(persoon3)
        
        self.session.commit()
        
        relatie1 = Relaties(persoonid1=persoon1.persoonId, persoonid2=persoon2.persoonId, relatietypeId=relatietype1.relatietypeId)
        relatie2 = Relaties(persoonid1=persoon1.persoonId, persoonid2=persoon3.persoonId, relatietypeId=relatietype2.relatietypeId)
        relatie3 = Relaties(persoonid1=persoon2.persoonId, persoonid2=persoon3.persoonId, relatietypeId=relatietype2.relatietypeId)
        self.session.add(relatie1)
        self.session.add(relatie2)
        self.session.add(relatie3)
        
        self.session.commit()

    def test_familie_persoon_relatie(self):
        familie = self.session.exec(select(Families).where(Families.familienaam == "De Vries")).first()
        self.assertIsNotNone(familie)
        self.assertEqual(len(familie.personen), 3)
        persoon_namen = [f"{p.voornaam} {p.achternaam}" for p in familie.personen]
        self.assertIn("Jan De Vries", persoon_namen)
        self.assertIn("Marie De Vries", persoon_namen)
        self.assertIn("Piet De Vries", persoon_namen)

    def test_persoon_jubileum_relatie(self):
        persoon = self.session.exec(select(Personen).where(Personen.voornaam == "Jan")).first()
        self.assertIsNotNone(persoon)
        self.assertEqual(persoon.jubileum.jubileumnaam, "Huwelijk")
        self.assertEqual(persoon.jubileum.jubileumdag, "2000-05-15")

    def test_persoon_relaties(self):
        jan = self.session.exec(select(Personen).where(Personen.voornaam == "Jan")).first()
        self.assertIsNotNone(jan)
        
        relaties = self.session.exec(select(Relaties).where(Relaties.persoonid1 == jan.persoonId)).all()
        self.assertEqual(len(relaties), 2)
        
        relatie_types = [self.session.get(Relatietypes, r.relatietypeId).relatienaam for r in relaties]
        self.assertIn("Echtgenoot", relatie_types)
        self.assertIn("Kind", relatie_types)

    def test_dubbele_relatie_preventie(self):
        jan = self.session.exec(select(Personen).where(Personen.voornaam == "Jan")).first()
        marie = self.session.exec(select(Personen).where(Personen.voornaam == "Marie")).first()
        echtgenoot_type = self.session.exec(select(Relatietypes).where(Relatietypes.relatienaam == "Echtgenoot")).first()
        
        # Probeer een dubbele relatie toe te voegen
        dubbele_relatie = Relaties(persoonid1=jan.persoonId, persoonid2=marie.persoonId, relatietypeId=echtgenoot_type.relatietypeId)
        self.session.add(dubbele_relatie)
        
        with self.assertRaises(Exception):  # Dit zou een IntegrityError moeten veroorzaken
            self.session.commit()
        
        self.session.rollback()

    def test_cascade_delete(self):
        # Test of het verwijderen van een familie ook alle gerelateerde personen verwijdert
        familie = self.session.exec(select(Families).where(Families.familienaam == "De Vries")).first()
        familie_id = familie.familieId
        self.session.delete(familie)
        self.session.commit()
        
        personen = self.session.exec(select(Personen).where(Personen.familieId == familie_id)).all()
        self.assertEqual(len(personen), 0)

if __name__ == '__main__':
    unittest.main()