import re

import bcrypt
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import LargeBinary
from models.db_model import Base, session

SERVICES = ["gestion", "commercial", "support"]


class Collaborator(Base):
    __tablename__ = 'collaborators'

    id = Column(Integer, primary_key=True)
    password = Column(LargeBinary(60), nullable=False)
    full_name = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)

    events = relationship(
        "Event", back_populates="support", foreign_keys="Event.support_id"
    )
    clients = relationship("Client", back_populates="commercial")

    def validate_full_name(self):
        if not self.full_name or not self.full_name.strip():
            raise ValueError("Le nom complet ne peut pas être vide.")
        existing_full_name = session.query(Collaborator).filter(
            Collaborator.full_name == self.full_name,
            Collaborator.id != getattr(self, "id", None)
        ).first()
        if existing_full_name:
            raise ValueError("Ce nom complet est déjà utilisé.")

    def validate_email(self):
        pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

        if not re.match(pattern, self.email):
            raise ValueError("Adresse e-mail invalide.")
        existing_email = session.query(Collaborator).filter(
            Collaborator.email == self.email,
            Collaborator.id != getattr(self, "id", None)
        ).first()
        if existing_email:
            raise ValueError("Cette adresse e-mail est déjà utilisée.")

    def validate_role(self):
        if self.role not in SERVICES:
            raise ValueError(
                f"Rôle invalide : {self.role}. Choisir parmi {SERVICES}.")

    def validate_all(self):
        self.validate_full_name()
        self.validate_email()
        self.validate_role()

    def set_password(self, raw_password: str):
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), salt)

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password)

    @staticmethod
    def filter_by_fields(**filters):
        """
        Filtre les clients selon les champs passés en tant qu'arguments de mot-clé.
        Exemple : Client.filter_by_fields(company_name="OpenAI", email="contact@openai.com")
        """
        query = session.query(Collaborator)
        for attr, value in filters.items():
            if hasattr(Collaborator, attr):
                query = query.filter(getattr(Collaborator, attr) == value)
        return query.all()

    @staticmethod
    def order_by_field(field_name: str, descending: bool = False):
        """
        Trie les collorateurs selon un champ spécifique.
        Exemple : Collaborator.order_by_field("created_date", descending=True)
        """
        if hasattr(Collaborator, field_name):
            field = getattr(Collaborator, field_name)
            query = session.query(Collaborator).order_by(
                field.desc() if descending else field.asc())
            return query.all()
        return []

    def save(self):
        self.validate_all()
        session.add(self)
        session.commit()

    @staticmethod
    def delete(collaborator_id: int):
        collaborator = session.query(Collaborator).filter_by(
            id=collaborator_id).first()
        session.delete(collaborator)
        session.commit()
