from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class Families(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    familienaam: str
    straatnaam: str
    huisnummer: str
    huisnummer_toevoeging: Optional[str] = None
    postcode: str
    plaats: str
    
    personen: List["Personen"] = Relationship(back_populates="familie")

class Personen(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    voornaam: str
    achternaam: str
    familie_id: Optional[int] = Field(default=None, foreign_key="families.id")
    
    familie: Optional[Families] = Relationship(back_populates="personen")
    jubilea: List["Jubilea"] = Relationship(back_populates="persoon")
    relaties_als_persoon1: List["Relaties"] = Relationship(back_populates="persoon1", sa_relationship_kwargs={"foreign_keys": "[Relaties.persoon1_id]"})
    relaties_als_persoon2: List["Relaties"] = Relationship(back_populates="persoon2", sa_relationship_kwargs={"foreign_keys": "[Relaties.persoon2_id]"})

class Jubilea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    jubileumnaam: str
    jubileumdag: str
    persoon_id: int = Field(foreign_key="personen.id")
    
    persoon: Personen = Relationship(back_populates="jubilea")

class Relatietypes(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    relatienaam: str
    
    relaties: List["Relaties"] = Relationship(back_populates="relatietype")

class Relaties(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    persoon1_id: int = Field(foreign_key="personen.id")
    persoon2_id: int = Field(foreign_key="personen.id")
    relatietype_id: int = Field(foreign_key="relatietypes.id")
    
    persoon1: Personen = Relationship(back_populates="relaties_als_persoon1", sa_relationship_kwargs={"foreign_keys": "[Relaties.persoon1_id]"})
    persoon2: Personen = Relationship(back_populates="relaties_als_persoon2", sa_relationship_kwargs={"foreign_keys": "[Relaties.persoon2_id]"})
    relatietype: Relatietypes = Relationship(back_populates="relaties")