from datetime import date

from sqlalchemy import Date, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.contract import Contract
from models.collaborator import Collaborator
from models.db_model import Base, session


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    location = Column(String)
    participants = Column(Integer)
    notes = Column(Text)

    client_id = Column(Integer, ForeignKey('clients.id'))
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    support_id = Column(Integer, ForeignKey('collaborators.id'))

    client = relationship("Client", back_populates="events")
    contract = relationship("Contract", back_populates="event")
    support = relationship("Collaborator", back_populates="events")

    def validate_dates(self):
        if not isinstance(self.start_date, date) or not isinstance(self.end_date, date):
            raise ValueError("Les dates de début et de fin doivent être valides.")
        if self.start_date > self.end_date:
            raise ValueError("La date de début ne peut pas être après la date de fin.")

    def validate_title(self):
        if not self.title or not self.title.strip():
            raise ValueError("Le titre est requis.")

    def validate_participants(self):
        if not isinstance(self.participants, int) or self.participants < 0:
            raise ValueError("Le nombre de participants doit être un entier positif.")

    def validate_contract_id(self):
        contract = Contract.filter_by_fields(id=self.contract_id)
        if not contract:
            raise ValueError(f"Contrat ID {self.contract_id} introuvable.")
        if not contract.signed:
            raise ValueError(f"Le contrat n'est pas signé.")
        self.client_id = contract.client_id

    def validate_support_id(self):
        if self.support_id is not None:
            collaborator = session.query(Collaborator).filter_by(id=self.support_id).first()
            if not collaborator:
                raise ValueError(f"Collaborateur ID {self.support_id} introuvable.")

    def validate_all(self):
        self.validate_title()
        self.validate_dates()
        self.validate_participants()
        self.validate_contract_id()
        self.validate_support_id()

    @staticmethod
    def create(client_id, contract_id, title, start_date, end_date,
               location, participants, notes, support_id):
        event = Event(
            client_id=client_id,
            contract_id=contract_id,
            title=title,
            start_date=start_date,
            end_date=end_date,
            location=location,
            participants=participants,
            notes=notes,
            support_id=support_id
        )
        session.add(event)
        session.commit()
        return event

    def update(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        session.commit()

    @staticmethod
    def filter_by_fields(**filters):
        """
        Filtre les clients selon les champs passés en tant qu'arguments de mot-clé.
        Exemple : Client.filter_by_fields(company_name="OpenAI", email="contact@openai.com")
        """
        query = session.query(Event)
        for attr, value in filters.items():
            if hasattr(Event, attr):
                query = query.filter(getattr(Event, attr) == value)
        return query.all()

    @staticmethod
    def order_by_field(field_name: str, descending: bool = False):
        """
        Trie les clients selon un champ spécifique.
        Exemple : Client.order_by_field("created_date", descending=True)
        """
        if hasattr(Event, field_name):
            field = getattr(Event, field_name)
            query = session.query(Event).order_by(
                field.desc() if descending else field.asc())
            return query.all()
        return []