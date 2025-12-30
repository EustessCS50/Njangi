# Copilot / AI agent instructions — Njangi (Django)

This file gives concise, actionable guidance for an AI coding assistant working on this repository.

Project summary
- Minimal Django 6.0 project generated with `django-admin startproject`.
- Main app: `savingsapp` (directory: `Njangi/savingsapp`).
- Settings: [Njangi/settings.py](Njangi/Njangi/settings.py) (project-level configuration).
- Database: SQLite file at `Njangi/db.sqlite3` (configured in settings).

Essential workflows (copyable)
- Create virtualenv (Windows PowerShell):
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- From repository root the project `manage.py` lives under `Njangi/manage.py`. Common commands:
  - Run server: `python Njangi/manage.py runserver`
  - Apply migrations: `python Njangi/manage.py migrate`
  - Make migrations for `savingsapp`: `python Njangi/manage.py makemigrations savingsapp`
  - Run tests: `python Njangi/manage.py test`
  - Open shell: `python Njangi/manage.py shell`

Project-specific patterns and notes
- App registration: add new apps to `INSTALLED_APPS` in [Njangi/settings.py](Njangi/Njangi/settings.py). The app config class is `savingsapp.apps.SavingsappConfig`.
- URL routing: top-level `urlpatterns` currently only exposes the admin in [Njangi/urls.py](Njangi/Njangi/urls.py). Add `include('savingsapp.urls')` to expose app routes and create `savingsapp/urls.py` when adding views.
- Migrations: `savingsapp/migrations/` contains migration modules; keep migrations in-source with the repo (SQLite used in dev).
- Templates: none configured in `TEMPLATES['DIRS']` — prefer placing templates inside `savingsapp/templates/<appname>/` and enable if needed.

Dependencies & integration points
- See `requirements.txt` (Django==6.0, Pillow, tzdata, etc.). No external APIs or services are present in the repo.
- Persistence: using Django ORM with SQLite (`DATABASES` in settings). No additional DB adapters configured.

Codebase conventions to follow (discoverable)
- Follow standard Django layout already present (apps under `Njangi/`).
- Keep view logic in `savingsapp/views.py`, models in `savingsapp/models.py`, admin registrations in `savingsapp/admin.py`.
- Use `savingsapp.apps.SavingsappConfig` when referencing the app in `INSTALLED_APPS` to avoid name collisions.

Security / operational notes (observable)
- `SECRET_KEY` and `DEBUG = True` are checked into settings. Treat changes as local/dev-only; do not publish real secrets.

Examples (common edits an AI may perform)
- Add a model: edit `savingsapp/models.py`, then run `python Njangi/manage.py makemigrations savingsapp` and `migrate`.
- Add app URLs: create `savingsapp/urls.py`, then update [Njangi/urls.py](Njangi/Njangi/urls.py) with `path('', include('savingsapp.urls'))`.

If you are unsure
- Run the commands above in the repo root; `manage.py` is in the `Njangi/` subdirectory.
- If behavior differs locally, inspect `Njangi/Njangi/settings.py` for environment-specific overrides.

When merging or changing this file
- Preserve the short commands and the explicit paths (they are intentionally relative to repository root).

Feedback
- After updates, ask the human for missing conventions or CI/test workflows that aren't captured here.
