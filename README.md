# 🎉 EpicEvent 🎉
**EpicEvent** is a web management application for an event planning company.  
It allows you to:  
- Create collaborators divided into three departments (management, sales, and event support)  
- Create clients  
- Create service contracts  
- And finally, create event follow-up records.

It uses the user's role to define the actions they are allowed to perform in the application.

---

## 🚀 Main Features

- Management of events linked to client contracts  
- User authentication system via cookies  
- Validation and update interface with access control  
- Custom ORM based on SQLAlchemy without a framework  
- Management of sessions, permissions, and database rollback  
- Automated tests with `pytest` and `selenium`

---

## 🛠️ Technologies Used

- **Python 3.12+**
- **SQLAlchemy** (ORM)
- **SQLite**
- **Selenium** (UI tests)
- **Pytest** (unit, functional and integration tests)
- **Integrated Logging** (with `logger` per module and Sentry)

---


## 🧱 Architecture
```bash
Repository/
    ├── epic_event/                    # Code principal de l'application
    │   ├── models/             # ORM SQLAlchemy
    │   ├── static/             # Fichiers statiques (CSS, JS, images)
    │   ├── templates/          # Templates HTML  
    │   ├── render.engine.py    # Moteur de rendu HTML 
    │   ├── permission.py       # Gestion des permissions et des rôles
    │   ├── router.py           # Routage HTTP personnalisé
    │   ├── server.py           # Serveur HTTP personnalisé
    │   ├── settings.py         # Paramètres de configuration (port, DB, constantes)
    │   ├── views.py            # Logique métier et validation
    │   └── tests/              # Tests Selenium & Pytest
    ├── README.md
    └── requirements.txt
```

---
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
git clone https://github.com/Mikael2983/OC-P12_Develop_secure_back-end_architecture_with_Python_and_SQL.git
```
Then navigate inside the created folder

```bash
cd OC-P12_Develop_secure_back-end_architecture_with_Python_and_SQL
```

### 2. Create Virtual Environment

To create virtual environment, install virtualenv package of python and activate it by following command on terminal:

```bash
python -m venv .venv
```
for windows:
```bash
.venv\Scripts\activate
```
for Unix/MacOS :
```bash
source .venv/bin/acivate
```

### 3. Requirements

To install required python packages, copy requirements.txt file and then run following command on terminal:

```bash
pip install -r requirements.txt
```
### 4. Initialize Database

EpicEvent already contains the necessary data for tests or demos.

Depending on the server launch command, the corresponding data will be loaded.

### 5. Start Server

Then navigate inside the folder epic_event

```bash
cd epic_event
```
To see the data used for Pytest and Selenium tests, 

On the terminal enter following command to start the server::
```bash
python server.py test
```

To discover the application's features, enter following command to start the server:
```bash
python server.py demo
```

For your own usage, enter following command to start the server:

```bash
python server.py
```
### 6. Start the Webapp

To start the webapp on localhost, enter following URL in the web browser:

http://127.0.0.1:8000/


### 7. Connexion

To log in to a SUPERUSER account,
- with test database:

    Fill in the name: Admin and password: mypassword

    All test database accounts use the same password


- with others databases:
    
    Fill in the name: Admin User and password: adminpass.

    All demo database accounts use the password first name+pass.

    e.g: Alice Martin use alicepass as password

### 8. Tests

all the tests as well as the server intended for them are already configured

all you need is to enter the pytest command on the terminal.

```bash
pytest
```