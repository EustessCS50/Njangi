# Project Schematics — Njangi

This document describes the high-level structure and components of the Njangi project (current version).

Repository layout (top-level):

- `Njangi/` — Django project directory containing project settings and `manage.py`.
  - `manage.py` — Django CLI entrypoint.
  - `Njangi/` — project package with `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`.
- `savingsapp/` — main Django app providing the Njangi functionality:
  - `models.py` — domain models: `Member`, `Membership`, `Meeting`, `Contribution`, `Loan`, `Repayment`, `Expense`, `BankAccount`, `BankTransaction`, etc.
  - `views.py` — HTML views for the web UI (dashboard, members, contributions, loans, etc.).
  - `api/` — REST API implementation using Django REST Framework:
    - `serializers.py` — DRF serializers for models.
    - `views.py` — DRF viewsets for the API endpoints.
    - `urls.py` — router registration of API endpoints.
  - `templates/savingsapp/` — HTML templates used by the web UI and API help page.
  - `static/savingsapp/` — static assets (CSS, JS, images).
  - `migrations/` — Django migrations for the app.

Key routes and API endpoints (as implemented):

- Web UI: routed through `savingsapp.views` (templates under `templates/savingsapp/`).
- API base: provided by `savingsapp.api.urls` (registered with a DRF `DefaultRouter`).
  - `/api/members/` — CRUD members
  - `/api/memberships/` — CRUD memberships
  - `/api/meetings/` — CRUD meetings
  - `/api/contributions/` — CRUD contributions
  - `/api/loans/` — CRUD loans
  - `/api/repayments/` — CRUD repayments
  - `/api/expenses/` — CRUD expenses
  - `/api/bank/accounts/` — CRUD bank accounts
  - `/api/bank/transactions/` — CRUD bank transactions
  - `/api/token/` — obtain JWT token (login)
  - `/api/token/refresh/` — refresh JWT token
  - `/api/help/` — API documentation and usage help (added in this version)
  - `/api/groups/` — manage Njangi accounts (SaaS groups)

Multi-tenant / SaaS model

- The project now supports a SaaS-style grouping: a `Group` (Njangi account) scopes `Members`, `Meetings`, `BankAccount`s and other resources. Each Group is a separate tenant; users who manage multiple Groups switch accounts by logging into the appropriate Group (or using an account switching feature to be implemented later).


Authentication and security:

- The API uses JWT tokens (via `rest_framework_simplejwt`) for protected endpoints. Obtain tokens via `/api/token/`.

How the pieces interact:

- The `savingsapp` app contains models which are serialized by `savingsapp.api.serializers` and exposed through DRF viewsets in `savingsapp.api.views` and registered in `savingsapp.api.urls`.
- Web UI views render templates in `templates/savingsapp/` using data from the ORM.
- Static assets live under `savingsapp/static/savingsapp/`.

Developer / Maintainer:

- Besong E. Besong — primary developer of this project (current version).

Notes:

- This is a development snapshot. Settings contain `DEBUG = True` and a checked-in `SECRET_KEY` (do not use in production).
