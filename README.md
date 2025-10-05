# PetCare

A **household pet management web application** built with **Flask** and **SQLite**.  
Users can create or join households, add pets, and record daily or weekly timeline entries for each pet.



## Features
- Create or join a household with a unique join code  
- Add, edit, and delete pets  
- Log entries for each pet (feeding, notes, vet visits, etc.)  
- View members within each household  
- Update usernames and household nicknames from the Profile page  
- Minimal, pastel UI built with PicoCSS + custom theme  



## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/hibbakamas/petcare.git
cd petcare
````

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies

To run the app:

```bash
pip install -r requirements.txt
```

If you also want to run tests:

```bash
pip install -r requirements-dev.txt
```

### 4. Initialize the database

```bash
flask db upgrade
```

If migrations do not exist yet:

```bash
flask db init
flask db migrate
flask db upgrade
```

### 5. Run the app

```bash
flask run
```

Then open your browser at **[http://localhost:5000](http://localhost:5000)**



## Project Structure

```
app/
 ├── app.py           # Main entrypoint
 ├── __init__.py      # App factory (create_app)
 ├── models.py        # SQLAlchemy models
 ├── utils.py         # Helper functions
 ├── routes/          # API and UI blueprints
 ├── templates/       # Jinja2 HTML templates
 ├── static/          # styles.css (pastel theme)
 ├── db.py            # Database instance
 └── config.py        # Configuration classes
migrations/            # Flask-Migrate folder
tests/                 # Pytest tests
.env.example           # Example environment variables
.gitignore             # Ignored files (venv, cache, etc.)
requirements.txt
requirements-dev.txt
README.md
```


## Tech Stack

* **Flask** — Web framework
* **SQLite** — Lightweight relational database
* **SQLAlchemy** — Object-relational mapper
* **Flask-Migrate** — Database migrations
* **Jinja2** — Templating engine for HTML pages
* **Werkzeug** — Used for secure password hashing and utilities
* **PicoCSS** — Minimal pastel UI framework
* **Pytest** — Unit testing framework
* **GitHub** — Version control and project management

## Running Tests

To verify functionality:

```bash
pytest
```

For coverage:

```bash
pytest --cov=app
```

> Tests automatically use an **in-memory SQLite database**
> (`sqlite:///:memory:`) defined in `tests/conftest.py`,
> so no setup or external DB is needed.


## Notes for Reviewers

* The project runs locally with minimal setup (Python + dependencies).
* All HTML templates and static assets are included.
* The app can be launched simply by running `flask run` after installation.
* Tests are reproducible and isolated — they will not affect user data.



## Credits

Developed by **Hibba Kamas**
Bachelor in Computer Science & Artificial Intelligence
IE University, Fall 2025
