import re

from sqlalchemy import Date, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date, datetime
from models.db_model import Base, session


class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    company_name = Column(String)
    created_date = Column(Date)
    last_contact_date = Column(Date)
    id_commercial = Column(Integer, ForeignKey('collaborators.id'))

    contracts = relationship("Contract", back_populates="client")
    events = relationship("Event", back_populates="client")
    commercial = relationship("Collaborator", back_populates="clients")

    @staticmethod
    def validate_full_name(name):
        if isinstance(name, str) and name.strip():
            return name.strip()
        return None

    @staticmethod
    def validate_email(email):
        if not isinstance(email, str):
            return None
        email = email.strip()
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return email
        return None

    @staticmethod
    def validate_phone(phone):
        if phone is None:
            return None
        phone = str(phone).strip()
        if re.match(r"^\+?[0-9\s\-().]{7,20}$", phone):
            return phone
        return None

    @staticmethod
    def validate_company_name(company):
        if company is None:
            return None
        if isinstance(company, str) and company.strip():
            return company.strip()
        return None

    @staticmethod
    def validate_date(value):
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    @staticmethod
    def create(full_name, email, phone=None, company_name=None):
        client = Client(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            created_date=date.today(),
            last_contact_date=date.today()
        )
        session.add(client)
        session.commit()

    def update(self, data: dict):
        for attr, value in data.items():
            setattr(self, attr, value)
        session.commit()

    @staticmethod
    def filter_by_fields(**filters):
        """
        Filtre les clients selon les champs passés en tant qu'arguments de mot-clé.
        Exemple : Client.filter_by_fields(company_name="OpenAI", email="contact@openai.com")
        """
        query = session.query(Client)
        for attr, value in filters.items():
            if hasattr(Client, attr):
                query = query.filter(getattr(Client, attr) == value)
        return query.all()

    @staticmethod
    def order_by_field(field_name: str, descending: bool = False):
        """
        Trie les clients selon un champ spécifique.
        Exemple : Client.order_by_field("created_date", descending=True)
        """
        if hasattr(Client, field_name):
            field = getattr(Client, field_name)
            query = session.query(Client).order_by(field.desc() if descending else field.asc())
            return query.all()
        return []
