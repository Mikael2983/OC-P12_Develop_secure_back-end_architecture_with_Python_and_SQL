from datetime import date, timedelta

from models.client import Client
from models.collaborator import Collaborator
from models.contract import Contract
from models.event import Event

from models.db_model import session


def init_data_base():
    collaborators = session.query(Collaborator).all()
    if not collaborators:
        collaborators=[]
        collaborator = Collaborator(full_name="admin user", email="admin@epicevent.com", role="gestion")
        collaborator.set_password("adminpass")
        collaborators.append(collaborator)
        collaborator = Collaborator(full_name="Alice Martin", email="alice@epicevent.com", role="gestion")
        collaborator.set_password("alicepass")
        collaborators.append(collaborator)
        collaborator = Collaborator(full_name="Bruno Lefevre", email="bruno@epicevent.com", role="commercial")
        collaborator.set_password("brunopass")
        collaborators.append(collaborator)
        collaborator = Collaborator(full_name="Chloé Dubois", email="chloe@epicevent.com", role="commercial")
        collaborator.set_password("clhoepass")
        collaborators.append(collaborator)
        collaborator = Collaborator(full_name="David Morel", email="david@epicevent.com", role="support")
        collaborator.set_password("davidpass")
        collaborators.append(collaborator)
        collaborator = Collaborator(full_name="Emma Bernard", email="emma@epicevent.com", role="support")
        collaborator.set_password("emmapass")
        collaborators.append(collaborator)
        session.add_all(collaborators)
        session.flush()

        # Clients
        clients = [
            Client(full_name="Jean Dupont", email="jean@nova.com", phone="0102030405", company_name="Entreprise Nova",
                   created_date=date.today(), last_contact_date=date.today(), id_commercial=collaborators[1].id),
            Client(full_name="Sophie Durant", email="sophie@techline.com", phone="0605040302", company_name="Techline SARL",
                   created_date=date.today(), last_contact_date=date.today(), id_commercial=collaborators[2].id),
            Client(full_name="Marc Petit", email="marc@alphacorp.com", phone="0758493021", company_name="AlphaCorp",
                   created_date=date.today(), last_contact_date=date.today(), id_commercial=collaborators[1].id),
        ]
        session.add_all(clients)
        session.flush()

        # Contracts
        contracts = [
            Contract(total_amount="10000", amount_due="0", created_date=date.today() - timedelta(days=60), signed=True, client_id=clients[0].id),
            Contract(total_amount="8500", amount_due="0", created_date=date.today() - timedelta(days=45), signed=True, client_id=clients[1].id),
            Contract(total_amount="12000", amount_due="0", created_date=date.today() - timedelta(days=30), signed=True, client_id=clients[2].id),
            Contract(total_amount="15000", amount_due="0", created_date=date.today() - timedelta(days=15), signed=True, client_id=clients[0].id),
            Contract(total_amount="9500", amount_due="0", created_date=date.today() - timedelta(days=10), signed=True, client_id=clients[1].id),
            Contract(total_amount="6000", amount_due="6000", created_date=date.today() - timedelta(days=5), signed=False, client_id=clients[2].id),
            Contract(total_amount="11000", amount_due="11000", created_date=date.today(), signed=False, client_id=clients[0].id),
        ]
        session.add_all(contracts)
        session.flush()

        # Events
        today = date.today()
        events = [
            Event(title="Conférence TechNova", start_date=today - timedelta(days=40), end_date=today - timedelta(days=38),
                  location="Paris", participants=150, notes="Conférence terminée avec succès.",
                  client_id=clients[0].id, contract_id=contracts[0].id, support_id=collaborators[3].id),
            Event(title="Salon des Innovations", start_date=today - timedelta(days=30), end_date=today - timedelta(days=28),
                  location="Lyon", participants=200, notes="Salon très fréquenté.",
                  client_id=clients[1].id, contract_id=contracts[1].id, support_id=collaborators[4].id),
            Event(title="Séminaire Alpha", start_date=today - timedelta(days=20), end_date=today - timedelta(days=18),
                  location="Bordeaux", participants=100, notes="Retour très positif.",
                  client_id=clients[2].id, contract_id=contracts[2].id, support_id=collaborators[3].id),
            Event(title="Forum Digital", start_date=today + timedelta(days=5), end_date=today + timedelta(days=6),
                  location="Marseille", participants=80, notes="Préparation en cours.",
                  client_id=clients[0].id, contract_id=contracts[3].id, support_id=collaborators[4].id),
            Event(title="Atelier Startups", start_date=today + timedelta(days=10), end_date=today + timedelta(days=11),
                  location="Nice", participants=120, notes="Inscription ouverte.",
                  client_id=clients[1].id, contract_id=contracts[4].id, support_id=collaborators[3].id),
        ]
        session.add_all(events)
        session.commit()
