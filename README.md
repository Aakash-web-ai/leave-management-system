# LeaveDesk — Employee Leave Management System

A full-stack leave management web app built with Flask, SQLAlchemy, and MySQL.

## Features
- **Employee**: register/login, apply for leave, view leave balance by type, see request history, cancel pending requests
- **Manager**: review and approve/reject leave requests from direct reports
- **Admin**: manage employees and roles, configure leave types, view org-wide reports
- **Leave balance tracking**: balances are auto-created per employee/leave-type/year and auto-deducted when a request is approved
- Weekend-aware day counting (Sat/Sun excluded from leave day totals)

## Tech stack
- Backend: Flask, Flask-SQLAlchemy, Flask-Login
- Database: MySQL (via PyMySQL)
- Frontend: Jinja2 templates + custom CSS (no framework dependency)

## Project structure
```
leave_management/
├── app.py                  # App factory, DB init, seed data
├── config.py                # Loads settings from .env
├── models.py                # SQLAlchemy models
├── schema.sql                # Raw SQL schema (reference / manual setup)
├── requirements.txt
├── .env.example
├── routes/
│   ├── auth.py               # login/register/logout
│   ├── employee.py           # dashboard, apply leave, history
│   └── manager.py            # approvals, admin employee/leave-type/report views
├── templates/                # Jinja2 HTML templates
└── static/css/style.css      # Styling
```

## Setup

1. **Install MySQL** locally (or use a hosted instance) and make sure it's running.

2. **Create a virtual environment and install dependencies:**
   ```bash
   cd leave_management
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `DB_PASSWORD` (and other DB settings) to match your MySQL setup.

4. **Create the database:**
   ```bash
   mysql -u root -p -e "CREATE DATABASE leave_management;"
   ```
   You don't need to run `schema.sql` manually — the app creates all tables automatically
   on first run via `db.create_all()`. `schema.sql` is included as a reference/manual-setup option.

5. **Run the app:**
   ```bash
   python app.py
   ```
   Visit `http://127.0.0.1:5000`.

## Default admin login
On first run, the app auto-creates an admin account:
- Email: `admin@company.com`
- Password: `Admin@123`

**Change this password immediately** (or delete/edit the row in the `employees` table) before using this anywhere beyond local testing.

## How roles work
- New sign-ups via `/register` are created as `employee` by default.
- An **admin** can promote users to `manager` or `admin`, and assign an employee's manager, from the **Employees** page.
- **Managers** only see and act on leave requests from employees whose `manager_id` points to them.
- **Admins** see all requests, manage leave types, and view reports.

## Leave balance logic
- Each employee gets a balance row per leave type per calendar year, seeded from that leave type's `default_days_per_year`.
- Balances are checked at request time (can't apply for more days than remain) and again at approval time (in case something changed in between).
- `used_days` only increases when a manager/admin approves a request — rejected or cancelled requests never touch the balance.

## Notes / next steps you could add
- Email notifications on approval/rejection
- A calendar view of team leave
- Half-day leave support
- Password reset flow
- Carry-forward logic for unused leave at year-end
