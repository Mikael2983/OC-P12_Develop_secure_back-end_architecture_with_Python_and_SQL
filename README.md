# EpicEvent 🎉

**EpicEvent** est une application web de gestion de contrats clients pour une société d'organisation d'événements.  
Elle permet aux commerciaux de créer, modifier et valider des contrats, tout en assurant une architecture sécurisée et extensible côté back-end.

---

## 🚀 Fonctionnalités principales

- Gestion des événements liés aux contrats des clients
- Interface de validation et mise à jour avec contrôle d'accès
- ORM personnalisé basé sur SQLAlchemy sans framework
- Gestion des sessions, permissions et rollback de base de données
- Tests automatisés avec `pytest` et `selenium`

---

## 🛠️ Technologies utilisées

- **Python 3.12+**
- **SQLAlchemy** (ORM)
- **SQLite** 
- **Selenium** (tests UI)
- **Pytest** (tests unitaires et d’intégration)
- **Logging intégré** (avec `logger` par module sentry)

---

## 🧱 Architecture

epic_event/
    ├── app/                    # Code principal de l'application
    │   ├── models/             # ORM SQLAlchemy
    │   ├── static/             # Fichiers statiques (CSS, JS, images)
    │   ├── templates/          # Templates HTML  
    │   ├── render.engine.py    # Moteur de rendu HTML 
    │   ├── permission.py       # Gestion des permissions et des rôles
    │   ├── router.py           # Routage HTTP personnalisé
    │   ├── server.py           # Serveur HTTP personnalisé
    │   ├── settings.py         # Paramètres de configuration (port, DB, constantes)
    │   └── views.py            # Logique métier et validation
    ├── tests/                  # Tests Selenium & Pytest
    ├── README.md
    └── requirements.txt

## Setup
### Prérequis
Python must be installed beforehand.

If you work in a Linux or MacOS environment: Python is normally already installed. To check, open your terminal and type:
```bash
python --version or python3 --version
```
If Python is not installed, you can download it at the following address: [Download Python3](https://www.python.org/downloads)

You will also need the pip Python package installer which is included by default if you have a Python version >= 3.4. You can check that it is available through your command line, by entering: 
```bash
pip --version
```
You will also need Git to clone the application on your computer. Check your installation by typing
```bash
git --version Otherwise
```
choose and download the version of Git that corresponds to your installation: MacOS, Windows or Linux/Unix by clicking on the following link: [Download git](https://git-scm.com/downloads) Then run the file you just downloaded. Press Next at each window and then Install. During installation, leave all the default options as they work well. Git Bash is the interface for using Git on the command line.

### 1. Clone the Repository

First, open the command prompt in the folder where you want to drop the clone.

clone this repository to your local machine. 

```bash
git clone https://github.com/Mikael2983/OC_P9_Develop_web_application_using_Django.git
```
Then navigate inside the folder OC_P9_Develop_web_application_using_Django

```bash
cd OC_P9_Develop_web_application_using_Django
```

### 2. Create Virtual Environment

To create virtual environment, install virtualenv package of python and activate it by following command on terminal:

```bash
python -m venv env
```
for windows:
```bash
env\Scripts\activate
```
for Unix/MacOS :
```bash
source env/bin/acivate
```


### 3. Requirements

To install required python packages, copy requirements.txt file and then run following command on terminal:

```bash
pip install -r requirements.txt
```
### 4. initalize database

To initialize the database, start by applying migrations. 

```bash
python manage.py migrate
```
To properly view application functionality load data from dump_140325.json file 

```bash
python manage.py loaddata dump_140325.json
```

### 5. Start Server

On the terminal enter following command to start the server:

```bash
python manage.py runserver
```
To log in to a SUPERUSER account,

Fill in the ID: mikael and password: Invit1234
All test database accounts use the same password

### 6. Start the Webapp

To start the webapp on localhost, enter following URL in the web browser:

http://127.0.0.1:8000/