from sqlalchemy import Date, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from models.client import Client
from models.db_model import Base, session


class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    total_amount = Column(String)
    amount_due = Column(String)
    created_date = Column(Date)
    signed = Column(Boolean, default=False)

    client_id = Column(Integer, ForeignKey('clients.id'))

    client = relationship("Client", back_populates="contracts")
    event = relationship("Event",
                         back_populates="contract",
                         uselist=False
                         )

    def normalize_signed(self, raw_value):
        truthy = {"yes", "y", "true", "1", "oui", "o"}

        if isinstance(raw_value, bool):
            self.signed = raw_value

        elif isinstance(raw_value, str):
            val = raw_value.strip().lower()
            self.signed = val in truthy

        else:
            self.signed = bool(raw_value)

    def validate_amounts(self):
        try:
            total = float(self.total_amount)
            due = float(self.amount_due)
        except (ValueError, TypeError):
            raise ValueError("Montants invalides : doivent être des nombres.")

        if total < 0 or due < 0:
            raise ValueError("Les montants doivent être positifs.")
        if due > total:
            raise ValueError(
                "Le montant dû ne peut pas dépasser le montant total.")

    def validate_client_existence(self):
        if not self.client_id:
            raise ValueError("client_id manquant.")
        client = session.query(Client).filter_by(id=self.client_id).first()
        if not client:
            raise ValueError(f"Aucun client avec id={self.client_id} trouvé.")

    def validate_all(self):
        self.validate_amounts()
        self.validate_client_existence()
        if not isinstance(self.signed, bool):
            raise ValueError("Le champ 'signed' doit être un booléen.")

    @staticmethod
    def filter_by_fields(**filters):
        """
        Filtre les clients selon les champs passés en tant qu'arguments de mot-clé.
        Exemple : Client.filter_by_fields(company_name="OpenAI", email="contact@openai.com")
        """
        query = session.query(Contract)
        for attr, value in filters.items():
            if hasattr(Contract, attr):
                query = query.filter(getattr(Contract, attr) == value)
        return query.all()

    @staticmethod
    def order_by_field(field_name: str, descending: bool = False):
        """
        Trie les clients selon un champ spécifique.
        Exemple : Client.order_by_field("created_date", descending=True)
        """
        if hasattr(Contract, field_name):
            field = getattr(Contract, field_name)
            query = session.query(Contract).order_by(
                field.desc() if descending else field.asc())
            return query.all()
        return []
