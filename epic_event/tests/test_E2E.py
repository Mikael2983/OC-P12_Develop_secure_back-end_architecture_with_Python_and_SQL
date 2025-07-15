from datetime import datetime
import pytest
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from epic_event.models import Collaborator, Contract

login_dict = {
        "admin": {"full_name": "Admin", "password": "mypassword"},
        "commercial": {"full_name": "Dup", "password": "mypassword"},
        "gestion": {"full_name": "Alice", "password": "mypassword"},
        "support": {"full_name": "Bob", "password": "mypassword"}
    }


def login(driver, service):
    driver.get("http://localhost:5000")
    time.sleep(2)
    driver.find_element(By.ID, "full_name").send_keys(
        login_dict[service]["full_name"])
    driver.find_element(By.NAME, "password").send_keys(
        login_dict[service]["password"])
    driver.find_element(By.ID, "login_button").click()


def logout(driver):
    logout_button = driver.find_element(By.ID, "button_logout")
    logout_button.click()
    time.sleep(2)


def test_user_login(driver):
    driver.get("http://localhost:5000")
    time.sleep(2)
    full_name = driver.find_element(By.ID, "full_name")
    password = driver.find_element(By.NAME, "password")

    full_name.send_keys("Dup")
    password.send_keys("mypassword")

    login_button = driver.find_element(By.ID, "login_button")
    login_button.click()

    time.sleep(2)
    assert "Bienvenue, Dup" in driver.page_source


def test_user_logout(driver):
    login(driver, "commercial")
    time.sleep(2)

    logout_button = driver.find_element(By.ID, "button_logout")
    logout_button.click()
    time.sleep(2)

    assert "Welcome to the Epic Events CRM portal" in driver.page_source


def test_login_forbidden_get(driver):
    driver.get("http://localhost:5000/login")
    time.sleep(2)
    assert "403" in driver.page_source


def test_home_route(driver):
    driver.get("http://localhost:5000")
    time.sleep(2)
    assert "Welcome" in driver.page_source


def test_entities_list_view(driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators")
    time.sleep(2)
    assert "Liste des collaborateurs" in driver.page_source

    driver.get("http://localhost:5000/clients")
    time.sleep(2)
    assert "Liste des clients" in driver.page_source

    driver.get("http://localhost:5000/contracts")
    time.sleep(2)
    assert "Liste des contrats" in driver.page_source

    driver.get("http://localhost:5000/events")
    time.sleep(2)
    assert "Liste des événements" in driver.page_source


def test_entities_detail_view(driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/1")
    time.sleep(2)
    assert "Détail du collaborateur" in driver.page_source
    assert "Alice" in driver.page_source

    driver.get("http://localhost:5000/clients/1")
    time.sleep(2)
    assert "Détail du client" in driver.page_source
    assert "Client Test" in driver.page_source

    driver.get("http://localhost:5000/contracts/1")
    time.sleep(2)
    assert "Détail du contrat" in driver.page_source
    assert "TestCorp" in driver.page_source

    driver.get("http://localhost:5000/events/1")
    time.sleep(2)
    assert "Détail de l'événement" in driver.page_source
    assert "Annual Gala" in driver.page_source


def test_entity_create_get_view(driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/create")
    time.sleep(2)
    assert "Créer un collaborateur" in driver.page_source
    driver.get("http://localhost:5000/contracts/create")
    time.sleep(2)
    assert "Créer un contrat" in driver.page_source
    logout(driver)
    time.sleep(2)
    login(driver, "commercial")
    driver.get("http://localhost:5000/clients/create")
    time.sleep(2)
    assert "Créer un client" in driver.page_source
    driver.get("http://localhost:5000/events/create?contract_id=3")
    time.sleep(2)
    assert "Créer un événement" in driver.page_source
    logout(driver)


def test_entity_create_view_gestion_forbidden_access(driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/create")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/events/create?contract_id=3")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    logout(driver)


def test_entity_create_view_commercial_forbidden_access(driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/create")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/contracts/create")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    logout(driver)


def test_entity_create_view_support_forbidden_access(driver):
    login(driver, "support")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/create")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/clients/create")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/contracts/create")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/events/create?contract_id=3")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    logout(driver)


def test_Collaborator_create_post(driver):
    login(driver, "gestion")
    driver.get("http://localhost:5000/collaborators/create")
    time.sleep(2)
    driver.find_element(By.ID, "full_name").send_keys("Jean Test")
    driver.find_element(By.ID, "email").send_keys("jean.test@example.com")
    driver.find_element(By.ID, "password").send_keys("strongpass")
    Select(driver.find_element(By.ID, "service")).select_by_value("support")
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(2)
    assert "Jean Test" in driver.page_source
    logout(driver)


def test_Contract_create_post(driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/contracts/create")
    time.sleep(2)
    select_client = Select(driver.find_element(By.ID, "client_id"))
    select_client.select_by_index(0)
    driver.find_element(By.ID, "total_amount").send_keys("3000")
    driver.find_element(By.ID, "amount_due").send_keys("1200")
    select_signed = Select(driver.find_element(By.ID, "signed"))
    select_signed.select_by_value("True")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "3000" in driver.page_source or "Contrat" in driver.page_source
    logout(driver)


def test_Client_create_post(driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/create")
    time.sleep(2)
    driver.find_element(By.ID, "company_name").send_keys("Company France")
    driver.find_element(By.ID, "full_name").send_keys("Jean Dupont")
    driver.find_element(By.ID, "email").send_keys("jean.dupont@example.com")
    driver.find_element(By.ID, "phone").send_keys("0123456789")
    driver.find_element(By.ID, "last_contact_date").send_keys("08-07-2025")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    assert "Company France" in driver.page_source or "Jean Dupont" in driver.page_source
    logout(driver)


def test_Events_create_post(driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/events/create?contract_id=4")
    time.sleep(2)
    driver.find_element(By.ID, "title").send_keys("Conférence Test 2025")
    driver.find_element(By.ID, "start_date").send_keys("01-08-2025")
    driver.find_element(By.ID, "end_date").send_keys("02-08-2025")
    driver.find_element(By.ID, "location").send_keys(
        "Paris Expo Porte de Versailles")
    driver.find_element(By.ID, "participants").send_keys("200")
    driver.find_element(By.ID, "notes").send_keys(
        "Intervenants internationaux")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "Conférence Test 2025" in driver.page_source or "Paris Expo" in driver.page_source
    time.sleep(2)
    logout(driver)


def test_entity_update_get_view(driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/3/update")
    time.sleep(2)
    assert "Modifier le collaborateur" in driver.page_source
    driver.get("http://localhost:5000/contracts/1/update")
    time.sleep(2)
    assert "Modifier le contract" in driver.page_source
    time.sleep(2)
    driver.get("http://localhost:5000/events/1/update")
    time.sleep(2)
    assert "Assigner un collaborateur" in driver.page_source
    time.sleep(2)
    logout(driver)

    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/1/update")
    time.sleep(2)
    assert "Modifier le client" in driver.page_source
    logout(driver)
    login(driver, "support")
    time.sleep(2)
    driver.get("http://localhost:5000/events/1/update")
    time.sleep(2)
    assert "Modifier l'événement" in driver.page_source
    logout(driver)


def test_entity_update_view_forbidden_access(driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/1/update")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    logout(driver)

    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/1/update")
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/contracts/1/update")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/events/1/update")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    logout(driver)

    login(driver, "support")
    driver.get("http://localhost:5000/collaborators/2/update")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/clients/1/update")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    driver.get("http://localhost:5000/contracts/1/update")
    time.sleep(2)
    assert "accès refusé" in driver.page_source.lower()
    logout(driver)


def test_collaborator_update_post_view(db_session, driver):
    login(driver, "gestion")
    driver.get("http://localhost:5000/collaborators/3/update")
    time.sleep(2)
    driver.find_element(By.NAME, "full_name").send_keys("Bob Updated")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "Bob Updated" in driver.page_source
    driver.get("http://localhost:5000/collaborators/3/update")
    time.sleep(2)
    driver.find_element(By.NAME, "full_name").send_keys("Bob")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    logout(driver)


def test_contract_update_post_view(db_session, driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/contracts/1/update")
    time.sleep(2)
    driver.find_element(By.ID, "amount_due").send_keys("10")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "10" in driver.page_source


def test_event_update_post_view(db_session, driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/events/1/update")
    time.sleep(2)
    select_support = Select(driver.find_element(By.ID, "support_id"))
    select_support.select_by_index(0)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "Bob" in driver.page_source
    logout(driver)

    login(driver, "support")
    time.sleep(2)
    driver.get("http://localhost:5000/events/1/update")
    time.sleep(2)
    driver.find_element(By.ID, "participants").send_keys("250")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "250" in driver.page_source


def test_client_update_post_view(db_session, driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/1/update")
    time.sleep(2)
    driver.find_element(By.ID, "phone").send_keys("0601020304")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    assert "0601020304" in driver.page_source
    logout(driver)


def test_entity_password_view(driver, db_session):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/1/password")
    time.sleep(2)
    driver.find_element(By.NAME, "current_password").send_keys("mypassword")
    driver.find_element(By.NAME, "new_password").send_keys("alicepass")
    driver.find_element(By.NAME, "confirm_password").send_keys("alicepass")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    logout(driver)

    driver.find_element(By.ID, "full_name").send_keys("Alice")
    driver.find_element(By.NAME, "password").send_keys("alicepass")
    driver.find_element(By.ID, "login_button").click()
    time.sleep(2)
    assert "Bienvenue, Alice" in driver.page_source

    driver.get("http://localhost:5000/collaborators/1/password")
    time.sleep(2)
    driver.find_element(By.NAME, "current_password").send_keys("alicepass")
    driver.find_element(By.NAME, "new_password").send_keys("mypassword")
    driver.find_element(By.NAME, "confirm_password").send_keys("mypassword")
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)
    logout(driver)


def test_collaborator_delete(db_session, driver):
    login(driver, "gestion")
    time.sleep(2)
    collab = db_session.query(Collaborator).filter_by(full_name="Jean Test").first()
    driver.get(f"http://localhost:5000/collaborators/{collab.id}/")
    time.sleep(2)
    driver.find_element(By.ID, "item_delete").click()
    time.sleep(2)
    assert "Jean Test" not in driver.page_source

    contract = db_session.query(Contract).filter_by(total_amount="3000").first()
    driver.get(f"http://localhost:5000/contracts/{contract.id}/")
    time.sleep(2)
    driver.find_element(By.ID, "item_delete").click()
    time.sleep(2)
    assert "2025-07-01" not in driver.page_source

    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/2/")
    time.sleep(2)
    driver.find_element(By.ID, "item_delete").click()
    time.sleep(2)
    assert "Company France" not in driver.page_source


def test_entity_delete_post(driver):
    login(driver, "gestion")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators/create")
    time.sleep(2)
    driver.find_element(By.NAME, "full_name").send_keys("ToDelete")
    driver.find_element(By.NAME, "email").send_keys("todel@corp.com")
    driver.find_element(By.NAME, "role").send_keys("support")
    driver.find_element(By.NAME, "password").send_keys("1234")
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(2)

    driver.get("http://localhost:5000/collaborators")
    time.sleep(2)
    driver.find_element(By.PARTIAL_LINK_TEXT, "ToDelete").click()
    time.sleep(2)
    current_url = driver.current_url
    entity_id = current_url.strip("/").split("/")[-1]

    driver.get(f"http://localhost:5000/collaborators/{entity_id}/delete")
    time.sleep(1)
    assert "ToDelete" not in driver.page_source


def test_client_contact_post(driver):
    login(driver, "commercial")
    time.sleep(2)
    driver.get("http://localhost:5000/clients/1")
    time.sleep(2)
    driver.find_element(By.ID, "contact").click()
    time.sleep(2)
    assert str(datetime.today()).split(" ")[0] in driver.page_source


def test_toggle_archive_display(driver):

    login(driver, "admin")
    time.sleep(2)
    driver.get("http://localhost:5000/collaborators")
    time.sleep(2)
    driver.find_element(By.NAME, "show_archived").click()
    time.sleep(2)
    assert "ToDelete" in driver.page_source
    driver.find_element(By.NAME, "show_archived").click()
    time.sleep(2)
    assert "ToDelete" not in driver.page_source


def test_logout(driver):
    login(driver, "support")
    driver.get("http://localhost:5000/logout")
    assert "Welcome" in driver.page_source
