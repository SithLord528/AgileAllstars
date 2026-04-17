# SFWE 407/507 - AgileAllstars Course Project

# Team Composition:
* Scrum Master: Cayden Hearne
* Requirements Manager: Molly Auer
* Testing Manager: Beckham Davis
* Dev Ops Manager: Josh Dean
* UI / UX Manager: Sam Cohen
* Subject Matter Expert (SME) /  Product Owner: Dr. Diana Saldana Jimenez


# Project Overview:
The AgileAllstars Product Development Management System (PDMS) will allow users to manage a software development product backlog.

## Objectives:
The PDMS will allow software development teams to add tasks to the product backlog, set and change priority for tasks, move tasks from the backlog to a current sprint backlog, and then from the sprint backlog to the ready for test status. Once tested, failures will be recycled to the backlog, successes will be marked as complete and ready for release.

## Scope of Function:
**1. User Authentication and Access Control** - The system will provide a secure login interface for users such as developers, project managers, and stakeholders. Users will be authenticated and granted role-based access to projects and features based on their permissions.

**2. Project Creation and Configuration** - The system will allow project managers to create new projects, define project settings, select workflows, and assign team members. This enables teams to structure projects according to their development methodology.

**3. Issue Creation** - Users can create issues such as tasks, bugs, or user stories by entering relevant informaton including title, descripton, priority, due date, and assignee. This allows work items to be tracked throughout the project lifecycle.

**4. Issue Assignment and Management** - Project leads can assign or reassign issues to team members as project needs change. Assignees can update issue details and ownership as work progresses.

**5. Workflow and Status Tracking** - The system will support predefined workflows that allow issues to move through states such as To Do, In Progress, In Review, and Done. Status changes will be recorded for tracking and accountability.

**6. Sprint Planning and Backlog Management** - Agile teams can create and manage product backlogs, prioritize issues, and assign selected issues to sprints with defined start and end dates. This supports iterative development cycles.

**7. Role and Permission Management** - Administrators can configure user roles and permissions to control access to projects, issues, and administrative features. This helps maintain system security and data integrity.

**8. Audit and History Tracking** - The system will maintain a history of all issue changes, including status updates, assignments, and comments. This provides traceability and supports accountability.

## Tech Stack:
* **Python 3.11+** - Core language. Developed and tested on 3.14; CI runs against 3.11, 3.12, and 3.13.
* **Django 6.0** - Web framework handling views, forms, ORM, authentication, and the admin. We use two SQLite databases with a custom router (`AgileDBRouter`) to keep auth data separate from project/sprint data.
* **SQLite** - Two database files: `agile_auth.sqlite3` (users, sessions) and `agile_projects.sqlite3` (projects, sprints, backlog items, comments). No extra DB server needed.
* **Django Cache Framework** - Used with `LocMemCache` to track failed login attempts and enforce account lockout after 5 failures.
* **GitHub Actions** - CI pipeline auto-runs the full test suite on every push and pull request (see `.github/workflows/django-tests.yml`).

## Development Environment:

### Windows
1. Make sure you have **Python 3.11+** installed. Grab it from [python.org](https://www.python.org/downloads/) if you don't.
2. Open a terminal (PowerShell or Command Prompt) and clone the repo:
   ```
   git clone https://github.com/<your-org>/AgileAllstars.git
   cd AgileAllstars/AgileAllstars1
   ```
3. Create a virtual environment and activate it:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run migrations for both databases:
   ```
   python manage.py migrate --database=default
   python manage.py migrate --database=projects
   ```
6. Start the dev server:
   ```
   python manage.py runserver
   ```
7. Open your browser to `http://127.0.0.1:8000/` — register a new account and you're in.
8. To run the test suite:
   ```
   python manage.py test tests --settings=AgileAllstars.test_settings --verbosity=2
   ```

### Mac
1. Make sure you have **Python 3.11+** installed. You can use [Homebrew](https://brew.sh/): `brew install python`
2. Clone the repo and cd into the project:
   ```
   git clone https://github.com/<your-org>/AgileAllstars.git
   cd AgileAllstars/AgileAllstars1
   ```
3. Create a virtual environment and activate it:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run migrations for both databases:
   ```
   python3 manage.py migrate --database=default
   python3 manage.py migrate --database=projects
   ```
6. Start the dev server:
   ```
   python3 manage.py runserver
   ```
7. Open your browser to `http://127.0.0.1:8000/` — register a new account and you're in.
8. To run the test suite:
   ```
   python3 manage.py test tests --settings=AgileAllstars.test_settings --verbosity=2
   ```

### Linux
1. Make sure you have **Python 3.11+** installed. Most distros have it or you can get it via your package manager (e.g. `sudo apt install python3 python3-venv python3-pip`).
2. Clone the repo and cd into the project:
   ```
   git clone https://github.com/<your-org>/AgileAllstars.git
   cd AgileAllstars/AgileAllstars1
   ```
3. Create a virtual environment and activate it:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run migrations for both databases:
   ```
   python3 manage.py migrate --database=default
   python3 manage.py migrate --database=projects
   ```
6. Start the dev server:
   ```
   python3 manage.py runserver
   ```
7. Open your browser to `http://127.0.0.1:8000/` — register a new account and you're in.
8. To run the test suite:
   ```
   python3 manage.py test tests --settings=AgileAllstars.test_settings --verbosity=2
   ```
