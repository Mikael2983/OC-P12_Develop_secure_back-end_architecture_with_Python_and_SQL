import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

options = Options()
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(options=options)

# Helpers login/logout
login_dict = {
    "admin": {"full_name": "Admin User", "password": "adminpass"},
    "gestion": {"full_name": "Alice Martin", "password": "alicepass"},
    "commercial": {"full_name": "Bruno Lefevre", "password": "brunopass"},
    "nouveau_commercial": {"full_name": "Jean Martin", "password": "newpass"},
    "support": {"full_name": "Emma Bernard", "password": "emmapass"}
}


def login(driver, role):
    driver.get("http://localhost:8000")
    time.sleep(1)
    driver.find_element(By.ID, "full_name").send_keys(
        login_dict[role]["full_name"])
    driver.find_element(By.NAME, "password").send_keys(
        login_dict[role]["password"])
    driver.find_element(By.ID, "login_button").click()
    time.sleep(2)


def logout(driver):
    driver.find_element(By.ID, "button_logout").click()
    time.sleep(2)


# Connexion gestionnaire
driver.get("http://localhost:8000")
print("voici la page d’accueil du server CRM, design sobre minimaliste, "
      "le front-end n’étant pas du tout l’objectif ici. ")

input("appuyer sur enter pour continuer")
print("Connexion de l’utilisatrice Alice du service gestion.")
driver.find_element(By.ID, "full_name").send_keys("Alice Martin")
print("Avec son nom et son mot de passe.")
driver.find_element(By.NAME, "password").send_keys("alicepass")
input("appuyer sur enter pour continuer")
print("elle arrive sur la liste des collaborateurs. ")
driver.find_element(By.ID, "login_button").click()

print(
    "Les membres du service gestion peuvent voir un bouton 'créer un collaborateur'"
    "elle va cliquer dessus")
input("appuyer sur enter pour continuer")
print("voici le formulaire pour enregistrer un nouveau collaborateur.")
driver.find_element(By.ID, "create_collab").click()

input("appuyer sur enter pour continuer")

driver.find_element(By.ID, "full_name").send_keys("Jean Martin")
driver.find_element(By.ID, "email").send_keys("jean.martin@epicevent.com")
driver.find_element(By.ID, "password").send_keys("newpass")
Select(driver.find_element(By.ID, "service")).select_by_value("commercial")

print("Après l’avoir rempli et sélectionner le bon service.")
input("appuyer sur enter pour continuer")
driver.find_element(By.XPATH, "//button[@type='submit']").click()

print("le collaborateur apparaît bien dans la liste mais")
print("Son adresse mail pro ne correspond pas au standard de la société")
print("elle change cela, en cliquant sur le crayon sur la ligne à son nom")
# Modifier email
input("appuyer sur enter pour continuer")
print("Alice accède au formulaire de mis a jours d'un collaborateur")
driver.get("http://localhost:8000/collaborators/7/update")
time.sleep(1)
print("Elle renseigne la nouvelle valeur puis valide.")
driver.find_element(By.ID, "email").send_keys("jean@epicevent.com")
input("appuyer sur enter pour continuer")
print("et voilà la valeur a été mis a jour.")
driver.find_element(By.XPATH, "//button[@type='submit']").click()

print("Le detail des collaborateure permet de visualiser ses informations "
      "( hors mot de passe bien sûr)")
input("appuyer sur enter pour continuer")
# Chloé
driver.get("http://localhost:8000/collaborators")
time.sleep(1)
print("mais aussi, pour un commercial, les clients dont il a la charge.")
driver.find_element(By.PARTIAL_LINK_TEXT, "Chloé Dubois").click()
input("appuyer sur enter pour continuer")
# David
driver.get("http://localhost:8000/collaborators")
time.sleep(2)
print("Ou bien, pour les support, les événements qu’il a ou va organiser.")
driver.find_element(By.PARTIAL_LINK_TEXT, "David Morel").click()

print(
    "Les liens à gauche lui permettent de visualiser les listes correspondantes.")
input("appuyer sur enter pour continuer")

# Client
driver.get("http://localhost:8000/clients")
print("d’abord la liste des clients. "
      "j'attire votre attention sur les variations à la droite des tableaux"
      "suivant le rôle de l'utilisateur deux colonnes supplémentaires"
      "apparaîssent pour permettre la modification ou la suppression.")

input("appuyer sur enter pour continuer")
print("En sélectionnant un nom dans la liste,")
driver.get("http://localhost:8000/clients/1")
time.sleep(1)
print("Alice peut  visualiser le commercial en charge de ce client ainsi que"
      "l’historique du client, tout les contrats passés et en cours.")
# Contrats
input("appuyer sur enter pour continuer")
print("Ensuite elle a accès à la liste de contrats,")
driver.get("http://localhost:8000/contracts")
time.sleep(1)
print(" et à un bouton pour en créer un nouveau que nous verrons plus tard.")
input("appuyer sur enter pour continuer")
print("en sélectionnant un contrat dans la liste,")
driver.get("http://localhost:8000/contracts/1")
time.sleep(1)
print("ses détails s’affiche ainsi que, s’il y en a un, ceux  de "
      "l’événement lié.")
input("appuyer sur enter pour continuer")
# Événements
print("En enfin, la liste des événements.")
driver.get("http://localhost:8000/events")
time.sleep(1)
print("dans la colonne Collaborateur,"
      "un lien apparaît quand un collaborateur peut ou doit être assigner.")
input("appuyer sur enter pour continuer")
print("Et cliquant sur un nom de la colonne contact,")
driver.get("http://localhost:8000/events/1")
time.sleep(1)
print("elle affiche les détails de l’événement et les détails du client "
      "et du contrat liés.")
input("appuyer sur enter pour continuer")
# Déco gestionnaire → nouveau commercial
print("Voici pour le tour rapide des affichages que propose le CRM.")
logout(driver)
print(
    "Alice a créé un nouveau collaborateur. Laissons-le accéder à son compte.")

input("appuyer sur enter pour continuer")
login(driver, "nouveau_commercial")
time.sleep(2)
print("Comme recommander par la gestionnaire"
      "la première chose  c’est personnaliser son mot de passe."
      "Laissons le faire.")
input("appuyer sur enter pour continuer")
# Modifier mot de passe
driver.find_element(By.ID, "button_password").click()
driver.find_element(By.NAME, "current_password").send_keys("newpass")
driver.find_element(By.NAME, "new_password").send_keys("jeanpass")
driver.find_element(By.NAME, "confirm_password").send_keys("jeanpass")
login_dict["nouveau_commercial"]["password"] = "jeanpass"
time.sleep(1)
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(1)
print("Voilà, un message l’informe que son mot de passe a bien été modifié."
      "Il peut commencer à utiliser son compte utilisateur.")
input("appuyer sur enter pour continuer")
# Clients
print("C’est un gros bosseur et avec beaucoup de tchatche, et à peine arriver,"
      "il enregistre déjà un nouveau client.")
driver.get("http://localhost:8000/clients")
print("il clique sur le bouton 'créer un client'")
input("appuyer sur enter pour continuer")
# Nouveau client
driver.find_element(By.ID, "create_client").click()
time.sleep(2)
driver.find_element(By.ID, "company_name").send_keys("NewCo")
print("En fait luc, c’est son beau frère qui vient de lancer sa startup ")
time.sleep(1)
driver.find_element(By.ID, "full_name").send_keys("Luc Martin")
print("et il l’a convaincu qu’un pot de présentation dans le FabLab qui les ")
time.sleep(1)
driver.find_element(By.ID, "email").send_keys("luc@newco.com")
print("abrite serait un bon moyen de se faire connaître ")
time.sleep(1)
driver.find_element(By.ID, "phone").send_keys("0707070707")
print("et surtout de nous en confier l’organisation.  Donc Pourquoi pas..")
time.sleep(1)
driver.find_element(By.ID, "last_contact_date").send_keys("14-07-2025")
time.sleep(1)
input("appuyer sur enter pour continuer")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)
print("Voila le client est créé, il a discuté du projet avec le service de "
      "gestion qui va pouvoir créer un contrat.")
driver.get("http://localhost:8000/clients")

input("appuyer sur enter pour continuer")
# Déco → gestionnaire
logout(driver)
print("Retrouvons donc Alice pour l’enregistrement du contrat.")
login(driver, "gestion")
time.sleep(2)
# Nouveau contrat non signé
driver.get("http://localhost:8000/contracts/create")
time.sleep(1)
print("elle sélectionne le client dans le menu déroulant")
Select(driver.find_element(By.ID, "client_id")).select_by_value("4")
time.sleep(1)
print("Entre un montant total et un montant due. Le même car aucun acompte n’a"
      "été versé. Et enfin, elle sélectionne False pour la signature du "
      "contrat.")
driver.find_element(By.ID, "total_amount").send_keys("5000")
driver.find_element(By.ID, "amount_due").send_keys("5000")
time.sleep(1)
Select(driver.find_element(By.ID, "signed")).select_by_value("False")
input("appuyer sur enter pour continuer")
driver.find_element(By.XPATH, "//button[@type='submit']").click()

# Liste contrats
driver.get("http://localhost:8000/contracts")
print("Le contrat apparaît bien dans la liste. ")
input("appuyer sur enter pour continuer")

logout(driver)

print("Le contrat sous le bras, Jean retourne voir Luc qui signe. "
      "Donc il retourne voir sur son compte pour créer l’événement. "
      )
input("appuyer sur enter pour continuer")
login(driver, "nouveau_commercial")
# Liste contrats
driver.get("http://localhost:8000/contracts")
time.sleep(1)
print("Problème, il n’a pas relayé l’info au service de gestion donc le "
      "contrat n’est pas enregistré comme étant signé.")
input("appuyer sur enter pour continuer")
# Déco → gestionnaire
logout(driver)
print("Par chance, il se trouve qu’Alice a du temps libre.")
login(driver, "gestion")

# Détails contrat
driver.get("http://localhost:8000/contracts/8")
time.sleep(1)
print("Elle lui arrange ça vite fait.")

driver.get("http://localhost:8000/contracts/8/update")
Select(driver.find_element(By.ID, "signed")).select_by_value("True")
input("appuyer sur enter pour continuer")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)
print("Et voila, le contrat est validé comme signé.")
input("appuyer sur enter pour continuer")
# Déco → commercial
logout(driver)
login(driver, "nouveau_commercial")

print("Jean peut maintenant créer son premier événement.")
# Liste contrats
driver.get("http://localhost:8000/contracts")
time.sleep(2)

# Créer événement
driver.get("http://localhost:8000/events/create?contract_id=8")
driver.find_element(By.ID, "title").send_keys("pot de Lancement Produit")
driver.find_element(By.ID, "start_date").send_keys("20-07-2025")
driver.find_element(By.ID, "start_time").send_keys("16:00")
driver.find_element(By.ID, "end_date").send_keys("20-07-2025")
driver.find_element(By.ID, "end_time").send_keys("22:00")
driver.find_element(By.ID, "location").send_keys("FabLab de Lille")
driver.find_element(By.ID, "participants").send_keys("5000")
driver.find_element(By.ID, "notes").send_keys(
    "Événement stratégique. ça va être énorme")
time.sleep(1)
driver.find_element(By.XPATH, "//button[@type='submit']").click()
time.sleep(2)
print("Après la validation, l’événement est dans les startings block.")
time.sleep(2)
# Déco → gestionnaire
logout(driver)

print("L’équipe de gestion (toujours Alice)")
login(driver, "gestion")
# Liste événements
driver.get("http://localhost:8000/events")
time.sleep(2)
print("va pouvoir lui assigner un collaborateur. Mais qui?")
# Liste collaborateurs tri service
driver.get("http://localhost:8000/collaborators")
print("Elle cherche donc les membres de l’équipe de support ")
input("appuyer sur enter pour continuer")
print("en cliquant sur le lien de tri de la colonne service une premiere fois,")
driver.find_element(By.ID, "sort_role").click()
print("elle obtient un tri ascendant qui ne l’arrange pas vraiment")
input("appuyer sur enter pour continuer")
print("donc elle re-click dessus pour obtenir le tri descendant.")
driver.find_element(By.ID, "sort_role").click()
print("Voila l'équipe support apparaît en tête du tableau."
      "Elle  voit qu’il y a deux possibilités David ou Emma"
      "voyons voir qui a de la place")
input("appuyer sur enter pour continuer")
# Détails David
print("David a un forum de 80 personnes dans 4 jours, il doit être occupé.")
driver.find_element(By.PARTIAL_LINK_TEXT, "David Morel").click()
time.sleep(1)
input("appuyer sur enter pour continuer")
# Détails Emma
driver.get("http://localhost:8000/collaborators/?sort=role&order=desc")
print("Voyons Emma, et bien Emma n’a rien en cours depuis 3 semaines.")
driver.find_element(By.PARTIAL_LINK_TEXT, "Emma Bernard").click()
input("appuyer sur enter pour continuer")

# Détails événement
print("Elle assigne donc Emma à l’organisation l’événement.")
driver.get("http://localhost:8000/events/")
time.sleep(1)
driver.find_element(By.ID, "event_6").click()
time.sleep(1)
Select(driver.find_element(By.ID, "support_id")).select_by_visible_text(
    "Emma Bernard")
input("appuyer sur enter pour continuer")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
print("l'événement a été mis à jour")
input("appuyer sur enter pour continuer")

# Déco → Emma
logout(driver)
login(driver, "support")
print("Emma quand elle se connecte et qu’elle consulte son profil.")
# Liste contrats
driver.get("http://localhost:8000/collaborators/6/")
print("Voit un nouvel événement pour elle.")
time.sleep(5)

# Liste événements
driver.get("http://localhost:8000/events")
print("dans la liste des évenements, vous noterez la couleur grisée des crayons"
      "quand l'événement n'est pas modifiable par l'utilisateur.")
input("appuyer sur enter pour continuer")
# Détails événement
driver.get("http://localhost:8000/events/6/")
time.sleep(2)
print("elle Consulte les détails et note tout de suite une incohérence.")
print("La salle du fabLab de lille, c’est pas le zenith,"
      "donc max 150 personnes dans la salle de conférence.")
input("appuyer sur enter pour continuer")
# Modifier participants et note
driver.get("http://localhost:8000/events/6/update")
print("donc après avoir contacter le client, elle modifie l'événement.")
driver.find_element(By.ID, "participants").send_keys("150")
time.sleep(1)
driver.find_element(By.ID, "notes").send_keys("On va se calmer.")
time.sleep(1)
input("appuyer sur enter pour continuer")
driver.find_element(By.XPATH, "//button[@type='submit']").click()
print("la mise à jour de l'événement est effectué.")
input("appuyer sur enter pour continuer")
print("elle décide au passge de faire un peu de tri dans ces événements")
# Liste événements
driver.get("http://localhost:8000/events")
print("et clique sur la corbeille du premier")
input("appuyer sur enter pour continuer")
driver.get("http://localhost:8000/events/1/delete")
print("l'événement n'apparaît plus dans la liste")
input("appuyer sur enter pour continuer")

logout(driver)

login(driver, "admin")
print("voici le compte administrateur.")
print("il dispose en plus d'une case à cocher pour afficher les éléments qui "
      "ont été supprimé par les autres utilisateurs")
print("s'il coche la case")
input("appuyer sur enter pour continuer")
driver.find_element(By.NAME, "show_archived").click()
time.sleep(2)
driver.get("http://localhost:8000/events")
print("l'événement supprimé par Emma apparaît dans la liste")
input("appuyer sur enter pour continuer")
driver.find_element(By.NAME, "show_archived").click()
print("s'il décoche la case, l'événement disparaît")
input("appuyer sur enter pour continuer")

# Déconnexion
print("Voilà, qui termine la démonstration de la plateforme")
logout(driver)
time.sleep(2)

# Fermer
driver.quit()
