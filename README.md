# VehiCare

Full-stack Django app (templates frontend) with PostgreSQL on Supabase.

## Features
- Account registration with validation (required fields, valid and unique email, unique username, matching passwords, hashed passwords)
- Login / logout with clear messages; `@login_required` protection
- Role-based dashboards (Admin and Vehicle Owner); users cannot open the other role's dashboard by URL
- User profile (view and edit own name, email, contact number, photo)
- Public landing page and black-and-gold themed interface (Django templates)

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
1. Open `.env` and replace `DB_PASSWORD` with your Supabase database password.
2. Run:
```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Superusers automatically get the **Admin** role. Everyone who registers through the site is a **Vehicle Owner**.
