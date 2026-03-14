# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Standalone FastAPI procurement app — part of Smart ERP. Sibling to `commercial-backend/` (one level up). Both apps share the same PostgreSQL database (`smarterp`) and JWT secret (tokens are interoperable), but run as separate processes.

- Port: **8001**
- Docs: `http://localhost:8001/procurement/docs`
- Health: `http://localhost:8001/procurement/health`
- API prefix: `/api/procurement/...`

## Running Locally (Windows)

```bash
# From inside procurement/ — MUST use run.py on Windows
python run.py 8001
```

`run.py` sets `WindowsSelectorEventLoopPolicy` before uvicorn starts (required for psycopg3 async on Windows). `--reload` is enabled by default.

**Do NOT use `uvicorn app.main:app` directly on Windows** — it will crash with ProactorEventLoop errors.

## Database Migrations

```bash
# From inside procurement/
PYTHONPATH=. alembic upgrade head
PYTHONPATH=. alembic revision --autogenerate -m "description"
```

All procurement tables are prefixed `proc_`. Migration files are in `alembic/versions/`.

## Testing

No pytest suite — test via Postman collection: `SmartERP-Procurement.postman_collection.json`

## Critical Rules

### Auth — JWT is for API authentication ONLY

There is ONE credential (`admin@smart.com` / `admin`). The frontend application makes all API requests on behalf of all users using this single credential.

**NEVER use `user.sub` (JWT email) for business logic.** It does not identify a vendor, requestor, or any business entity. All business identifiers (vendor email, requestor email, etc.) must come from the request body/params.

`user.sub` is ONLY for verifying the request is authenticated. `require_role()` infrastructure exists but is not used — all endpoints use `get_current_user` only.

### ⚠️ OPEN: Vendor/User Authentication — Needs Client Input

The spec defines 5 roles: **Procurement Head**, **Vendor**, **Requestor**, **Regional Manager**, **Site Manager**. Currently we use a single hardcoded credential and no role enforcement.

**Unresolved questions (ask client before implementing):**
1. Should this backend handle vendor/user login (credentials in our DB, JWT identifies the user)?
2. Or will a separate auth service / SSO handle it?
3. If we handle it: do vendors get credentials when invited (`POST /vendors`), or through a separate registration flow?
4. Once auth is real, should we derive `vendorCode` from JWT instead of requiring it in request body?
5. **User-site assignments:** The spec says `GET /user-sites` returns only sites assigned to the logged-in user, but no user↔site mapping table exists anywhere in the shared DB (commercial app doesn't have one either). Who manages this mapping — commercial app, a separate admin service, or the client's HR/identity system? Procurement can't build this alone since it doesn't manage users or site assignments.

Until decided, keep the current approach: single credential, business identifiers in request body, no role restrictions. `GET /user-sites` returns all sites (unfiltered).

### IDs — Human-readable business codes, NO UUIDs

All entity IDs use the format `{PREFIX}{N:07d}` — a short prefix + 7 zero-padded digits. This is the ONLY identifier — it serves as both the DB primary key and the API identifier. No UUIDs anywhere unless explicitly confirmed.

| Entity | Prefix | Example |
|--------|--------|---------|
| Vendor | VEN | VEN0000001 |
| Product | PRD | PRD0000001 |
| Indent | IND | IND0000001 |
| Purchase Order | PO | PO0000001 |
| Invoice | INV | INV0000001 |
| Cash Purchase | CP | CP0000001 |
| Machinery Req | MREQ | MREQ0000001 |
| Uniform Req | UNF | UNF0000001 |

Child/junction tables (items, links) without their own business ID use `SERIAL` integer PK.

Overflow: `{n:07d}` naturally expands to 8+ digits. No truncation, no collision.

### Single Auth Credential

Do NOT add role-based restrictions (`require_role()`) to endpoints. The number of credentials and role assignments is decided by the client, not assumed from the spec.

## Architecture

Each business module under `app/procurement/` follows a four-file pattern:

- `router.py` — FastAPI endpoints, uses `Depends(get_db)` and `Depends(get_current_user)`
- `service.py` — Business logic and async DB queries (SQLAlchemy 2.0)
- `models.py` — SQLAlchemy ORM models (`Mapped[]`, `mapped_column()`)
- `schemas.py` — Pydantic v2 schemas with `model_config = {"from_attributes": True}`

**Naming:** Pydantic schemas use **camelCase** (frontend contract). SQLAlchemy models use **snake_case**.

### Response Wrapper

All successful responses are wrapped via `success_response()` from `app/shared/schemas.py`:
```json
{"responseId": "uuid", "timestamp": "iso8601", "results": <spec response data>}
```
Errors use `ApiErrorResponse` with `errors[]` array of `{errorType, errorMessage, location}`.

### File Storage

MinIO via `app/shared/file_storage.py`. Bucket: `smarterp-procurement`.

Files are stored with human-readable paths: `vendor-applications/VEN0000001/panNo.pdf` (not UUID filenames).

`upload_fastapi_file(file, object_name="path/name.ext")` for explicit names, or `upload_fastapi_file(file, prefix="path")` for auto-generated names.

## Router Registration

Single resource path → dedicated prefix:
```python
app.include_router(indents_router, prefix="/api/procurement/indents", tags=["Indents"])
```

Multiple sub-paths (machinery, uniforms, sites) → base prefix, routes define paths internally:
```python
app.include_router(machinery_router, prefix="/api/procurement", tags=["Machinery"])
```

Vendors split: `vendors_router` at `/vendors`, `applications_router` at `/vendor-applications`.

## Modules

| Module | DB Tables | Key ID Format |
|---|---|---|
| vendors | proc_vendors (PK: vendor_code), proc_vendor_applications | VEN0000001 |
| products | proc_products, proc_product_price_change_requests | PRD0000001 |
| indents | proc_indents, proc_indent_items | IND0000001 |
| purchase_orders | proc_purchase_orders, proc_po_items, proc_grns, proc_grn_items, proc_grn_photos | PO0000001 |
| invoices | proc_invoices, proc_invoice_po_links | INV0000001 |
| cash_purchases | proc_cash_purchases | CP0000001 |
| machinery_requests | proc_machinery_requests, proc_machinery_purchase_orders, proc_machinery_grns | MREQ0000001 |
| uniform_requests | proc_uniform_requests, proc_uniform_purchase_orders | UNF0000001 |
| notifications | proc_notifications | — |
| logging | proc_api_logs (auto via middleware) | — |
| extra_material_requests | proc_extra_material_requests | — |
| sites | no tables (queries commercial data) | — |

## Spec Alignment (In Progress)

`Procurement_API_Specification.md` is the authoritative API spec (~110 endpoints). Implementation is being corrected to match it **5 endpoints at a time**, in spec order. After each batch:
1. Update `docs/endpoints.md`
2. Update `SmartERP-Procurement.postman_collection.json`
3. Update `docs/database_design.md` if schema changed

Key cross-cutting changes needed:
- Add pagination (`currentPage, totalPages, totalItems`) to all list endpoints
- Convert several endpoints from JSON to `multipart/form-data` (vendor applications, PO updates, GRN, invoices, cash purchases)
- Rename `rejectionReason` → `reason` on all reject endpoints
- Spec responses go inside the `success_response()` wrapper

## Import Convention

All imports: `from app.procurement.<module>.<file> import ...` or `from app.shared.<file> import ...`

**Never** use `from procurement.*`.

## Environment

Copy `.env.example` to `.env`. Critical vars:
- `DATABASE_URL` — `postgresql+psycopg://smarterp_dev:smarterp_dev@localhost:5432/smarterp`
- `JWT_SECRET_KEY` — must match commercial app
- `MINIO_*` — object storage config (MinIO server must be running on localhost:9000)

## Windows Notes

- Kill server: `powershell.exe -Command "Stop-Process -Id <PID> -Force"` (don't use `taskkill /F /PID` in bash)
- After editing code, wait ~2s for `--reload` — no restart needed
- Only restart if an alembic migration was added
- Always activate venv: `source .venv/Scripts/activate` before running python/alembic
