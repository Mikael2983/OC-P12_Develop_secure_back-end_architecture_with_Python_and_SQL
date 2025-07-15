import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# Helpers login/logout
login_dict = {
    "gestion": {"full_name": "Alice Martin", "password": "alicepass"},
    "commercial": {"full_name": "Bruno Lefevre", "password": "brunopass"},
    "nouveau_commercial": {"full_name": "Jean Martin", "password": "newpass"},
    "support": {"full_name": "Emma Bernard", "password": "emmapass"}
}

# Initialisation driver
driver = webdriver.Chrome()


def login(driver, role):
    driver.get("http://localhost:8000")
    time.sleep(1)
    driver.find_element(By.ID, "full_name").send_keys(login_dict[role]["full_name"])
    driver.find_element(By.NAME, "password").send_keys(login_dict[role]["password"])
    driver.find_element(By.ID, "login_button").click()
    time.sleep(2)


def logout(driver):
    driver.find_element(By.ID, "button_logout").click()
    time.sleep(2)


# Connexion gestionnaire
driver.get("http://localhost:8000")
input()

driver.find_element(By.ID, "full_name").send_keys("Alice Martin")
time.sleep(1)
driver.find_element(By.NAME, "password").send_keys("alicepass")
time.sleep(1)
driver.find_element(By.ID, "login_button").click()

time.sleep(1)

# Création nouveau commercial
driver.find_element(By.ID, "create_collab").click()
time.sleep(1)
driver.find_element(By.ID, "full_name").send_keys("Jean Martin")
driver.find_element(By.ID, "email").send_keys("jean.martin@epicevent.com")
driver.find_element(By.ID, "password").send_keys("newpass")
Select(driver.find_element(By.ID, "service")).select_by_value("commercial")
time.sleep(1)
driver.find_element(By.XPATH, "//button[@type='submit']").click()

time.sleep(1)

# Modifier email
driver.get("http://localhost:8000/collaborators/7/update")
time.sleep(1)
driver.find_element(By.ID, "email").send_keys("jean@epicevent.com")
time.sleep(2)
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(1)

# Chloé
driver.get("http://localhost:8000/collaborators")
time.sleep(2)
driver.find_element(By.PARTIAL_LINK_TEXT, "Chloé Dubois").click()
time.sleep(1)

# David
driver.get("http://localhost:8000/collaborators")
time.sleep(2)
driver.find_element(By.PARTIAL_LINK_TEXT, "David Morel").click()
time.sleep(1)

# Client
driver.get("http://localhost:8000/clients")
time.sleep(1)
driver.get("http://localhost:8000/clients/1")
time.sleep(1)

# Contrats
driver.get("http://localhost:8000/contracts")
time.sleep(1)
driver.get("http://localhost:8000/contracts/1")
time.sleep(1)

# Événements
driver.get("http://localhost:8000/events")
time.sleep(1)
driver.get("http://localhost:8000/events/1")
time.sleep(1)

# Déco gestionnaire → nouveau commercial
logout(driver)
login(driver, "nouveau_commercial")
time.sleep(2)
# Modifier mot de passe
driver.find_element(By.ID, "button_password").click()
driver.find_element(By.NAME, "current_password").send_keys("newpass")
time.sleep(1)
driver.find_element(By.NAME, "new_password").send_keys("jeanpass")
time.sleep(1)
driver.find_element(By.NAME, "confirm_password").send_keys("jeanpass")
time.sleep(1)
login_dict["nouveau_commercial"]["password"] = "jeanpass"
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(1)

# Clients
driver.get("http://localhost:8000/clients")
time.sleep(2)

# Nouveau client
driver.get("http://localhost:8000/clients/create")
time.sleep(2)
driver.find_element(By.ID, "company_name").send_keys("NewCo")
time.sleep(1)
driver.find_element(By.ID, "full_name").send_keys("Luc Martin")
time.sleep(1)
driver.find_element(By.ID, "email").send_keys("luc@newco.com")
time.sleep(1)
driver.find_element(By.ID, "phone").send_keys("0707070707")
time.sleep(1)
driver.find_element(By.ID, "last_contact_date").send_keys("14-07-2025")
time.sleep(1)
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)

# Liste clients
driver.get("http://localhost:8000/clients")
time.sleep(2)

# Déco → gestionnaire
logout(driver)
login(driver, "gestion")

# Nouveau contrat non signé
driver.get("http://localhost:8000/contracts/create")
time.sleep(1)
Select(driver.find_element(By.ID, "client_id")).select_by_value("4")
time.sleep(1)
driver.find_element(By.ID, "total_amount").send_keys("5000")
driver.find_element(By.ID, "amount_due").send_keys("5000")
time.sleep(1)
Select(driver.find_element(By.ID, "signed")).select_by_value("False")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)

# Liste contrats
driver.get("http://localhost:8000/contracts")
time.sleep(2)

# Déco → commercial
logout(driver)
login(driver, "nouveau_commercial")

# Liste contrats
driver.get("http://localhost:8000/contracts")
time.sleep(1)

# Déco → gestionnaire
logout(driver)
login(driver, "gestion")

# Détails contrat
driver.get("http://localhost:8000/contracts/8")
time.sleep(1)

# Signed = True
driver.get("http://localhost:8000/contracts/8/update")
Select(driver.find_element(By.ID, "signed")).select_by_value("True")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)

# Déco → commercial
logout(driver)
login(driver, "nouveau_commercial")

# Liste contrats
driver.get("http://localhost:8000/contracts")
time.sleep(2)

# Créer événement
driver.get("http://localhost:8000/events/create?contract_id=8")
driver.find_element(By.ID, "title").send_keys("pot de Lancement Produit")
time.sleep(1)
driver.find_element(By.ID, "start_date").send_keys("20-07-2025")
time.sleep(1)
driver.find_element(By.ID, "end_date").send_keys("20-07-2025")
time.sleep(1)
driver.find_element(By.ID, "location").send_keys("FabLab de Lille")
time.sleep(1)
driver.find_element(By.ID, "participants").send_keys("5000")
time.sleep(1)
driver.find_element(By.ID, "notes").send_keys("Événement stratégique. ça va être énorme")
time.sleep(1)
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)

# Déco → gestionnaire
logout(driver)
login(driver, "gestion")

# Liste événements
driver.get("http://localhost:8000/events")
time.sleep(2)

# Liste collaborateurs tri service
driver.get("http://localhost:8000/collaborators")
time.sleep(2)
driver.find_element(By.ID, "sort_role").click()
time.sleep(2)
driver.find_element(By.ID, "sort_role").click()
time.sleep(2)

# Détails David
driver.find_element(By.PARTIAL_LINK_TEXT, "David Morel").click()
time.sleep(2)

# Détails Emma
driver.get("http://localhost:8000/collaborators")
driver.find_element(By.PARTIAL_LINK_TEXT, "Emma Bernard").click()
time.sleep(2)

# Détails événement
driver.get("http://localhost:8000/events/")
time.sleep(1)
driver.get("http://localhost:8000/events/6")
time.sleep(2)

# Assigner Emma
driver.get("http://localhost:8000/events/6/update")
Select(driver.find_element(By.ID, "support_id")).select_by_visible_text("Emma Bernard")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)

# Déco → Emma
logout(driver)
login(driver, "support")

# Liste contrats
driver.get("http://localhost:8000/contracts")
time.sleep(2)

# Liste événements
driver.get("http://localhost:8000/events")
time.sleep(2)

# Détails événement
driver.get("http://localhost:8000/events/6/")
time.sleep(2)

# Modifier participants et note
driver.get("http://localhost:8000/events/6/update")
driver.find_element(By.ID, "participants").clear()
driver.find_element(By.ID, "participants").send_keys("500")
time.sleep(1)
driver.find_element(By.ID, "notes").send_keys("On va se calmer.")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)

# Liste événements
driver.get("http://localhost:8000/events")
time.sleep(2)

# Déconnexion
logout(driver)

# Fermer
driver.quit()
