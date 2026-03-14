# Procurement FastAPI Backend — Implementation Plan (v2)

## Context

Standalone FastAPI app inside `procurement/` (sibling to `commercial-backend/`).
Both apps share the same PostgreSQL DB (`smarterp`) but run on separate pods.

**Directory convention:**
- `procurement/` = repo root (same as `commercial-backend/`)
- `procurement/app/` = Python source package (same as `commercial-backend/app/`)
- All imports: `from app.*`
- Run: `uvicorn app.main:app --port 8001` (from inside `procurement/`)

---

## Deployment

**Local (Windows 11):**
```bash
# Terminal 1 — commercial (from commercial-backend/)
uvicorn app.main:app --port 8000 --reload

# Terminal 2 — procurement (from procurement/)
uvicorn app.main:app --port 8001 --reload
```

**Linux / Nginx routing:**
```nginx
location /api/commercial/ { proxy_pass http://localhost:8000; }
location /api/procurement/ { proxy_pass http://localhost:8001; }
```

---

## Auth Strategy

- Own login endpoint: `POST /api/procurement/auth/login`
- Same JWT secret + token format as commercial → tokens are interoperable
- Hardcoded credentials for dev (TODO: DB users table)

**Dev credentials:**
| email | password | role |
|---|---|---|
| admin@smart.com | admin | procurement_head |
| vendor@smart.com | vendor | vendor |
| requestor@smart.com | requestor | requestor |
| rm@smart.com | rm | regional_manager |
| sm@smart.com | sm | site_manager |

---

## Directory Structure

```
procurement/
├── app/
│   ├── __init__.py
│   ├── main.py                    ← FastAPI app; docs at /procurement/docs
│   ├── config.py                  ← Pydantic Settings
│   ├── database.py                ← Async SQLAlchemy + Base + get_db
│   ├── auth/
│   │   ├── dependencies.py        ← get_current_user, require_role, create_access_token
│   │   ├── schemas.py             ← LoginRequest, TokenResponse, TokenPayload
│   │   └── router.py              ← POST /api/procurement/auth/login
│   ├── shared/
│   │   ├── schemas.py             ← ApiResponse, success_response, ErrorDetail
│   │   ├── excel_utils.py
│   │   └── file_storage.py        ← MinIO (bucket: smarterp-procurement)
│   ├── logging/
│   │   ├── middleware.py          ← RequestLoggingMiddleware → proc_api_logs
│   │   ├── models.py              ← ProcApiLog
│   │   └── schemas.py
│   ├── vendors/                   ← proc_vendors, proc_vendor_applications
│   ├── products/                  ← proc_products, proc_product_price_change_requests
│   ├── sites/                     ← no DB table; queries commercial data
│   ├── extra_material_requests/   ← proc_extra_material_requests
│   ├── indents/                   ← proc_indents, proc_indent_items
│   ├── purchase_orders/           ← proc_purchase_orders, proc_po_items, proc_grns, proc_grn_items, proc_grn_photos
│   ├── invoices/                  ← proc_invoices, proc_invoice_po_links
│   ├── cash_purchases/            ← proc_cash_purchases
│   ├── machinery_requests/        ← proc_machinery_requests, proc_machinery_purchase_orders, proc_machinery_grns
│   ├── uniform_requests/          ← proc_uniform_requests, proc_uniform_purchase_orders
│   └── notifications/             ← proc_notifications
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_procurement_initial.py
├── alembic.ini
├── requirements.txt
├── Dockerfile                     ← port 8001; health at /procurement/health
├── .env.example
└── PLAN.md                        ← this file
```

---

## Router Registration Pattern (main.py)

Modules with routes at a single sub-path → dedicated prefix:
```python
app.include_router(indents_router,   prefix="/api/procurement/indents",   tags=["Indents"])
app.include_router(invoices_router,  prefix="/api/procurement/invoices",  tags=["Invoices"])
```

Modules with routes at multiple different sub-paths (machinery, uniforms, sites) →
prefix `/api/procurement` and routes define their own relative paths:
```python
app.include_router(machinery_router, prefix="/api/procurement", tags=["Machinery"])
# inside router: @router.get("/machinery-requests"), @router.get("/purchase-orders/machinery/...")
```

Vendors split into two routers:
```python
app.include_router(vendors_router,              prefix="/api/procurement/vendors",              tags=["Vendors"])
app.include_router(vendor_applications_router,  prefix="/api/procurement/vendor-applications",  tags=["Vendor Applications"])
```

---

## Migrations

```bash
# From inside procurement/
alembic upgrade head

# Or from repo root:
cd procurement && alembic upgrade head
```

---

## Verification (Phase 1)

```bash
# Start the app (from inside procurement/)
uvicorn app.main:app --port 8001 --reload

# Health check
GET http://localhost:8001/procurement/health
# → {"status": "healthy", "service": "Smart ERP Procurement"}

# Docs
GET http://localhost:8001/procurement/docs

# Login (procurement_head)
POST http://localhost:8001/api/procurement/auth/login
{"email": "admin@smart.com", "password": "admin"}
# → {"results": {"access_token": "...", "token_type": "bearer"}}

# Login (vendor)
POST http://localhost:8001/api/procurement/auth/login
{"email": "vendor@smart.com", "password": "vendor"}
```

---

## Implementation Phases

| Phase | Status | Description |
|---|---|---|
| 1 — Skeleton | ✅ DONE | All files, stubs, auth login, alembic migration |
| 2 — Vendors & Products | ✅ DONE | Registration, application, approval, bulk upload |
| 3 — Indents & EMR | ✅ DONE | Extra material permission, indent creation & approval |
| 4 — Purchase Orders & GRN | ✅ DONE | PO management, delivery status, GRN submission |
| 5 — Invoices & Cash Purchases | ✅ DONE | Invoice upload/validation, cash purchase flow |
| 6 — Machinery | ✅ DONE | Machinery requests, POs, GRN, invoices |
| 7 — Uniforms | ✅ DONE | Uniform requests, POs, GRN, invoices |
| 8 — Notifications | ✅ DONE | Notification creation, list, mark-as-read |
| 9 — Real Auth | TODO | Replace hardcoded credentials with DB users table |
| 10 — PDF Downloads | TODO | Implement 5 stub endpoints using reportlab/weasyprint |

---

## Pending: Real Authentication (Phase 9)

Both procurement and commercial currently use hardcoded credentials with a `# TODO` comment.
This must be resolved before dev deployment. Requires alignment with the commercial developer.

### What needs to happen

**Commercial developer's responsibility:**
1. Design the `users` table schema (see proposed schema below)
2. Write the Alembic migration in `commercial-backend/` to create it
   - Migration = a Python file that runs `CREATE TABLE users (...)` on any environment
   - Run once per environment: `alembic upgrade head`
3. Build user management endpoints in commercial (create/update/deactivate users)

**Procurement's responsibility (after commercial creates the table):**
1. Add a read-only `User` mirror model pointing at the shared `users` table
   (same pattern as `Site` model — no migration needed, just read)
2. Update `app/auth/router.py` login endpoint to query `users` table
   instead of the hardcoded dict
3. Hash password comparison using `bcrypt` (passwords stored as hashes, never plain text)

### Proposed `users` table schema

```sql
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,   -- bcrypt hash, never plain text
    full_name   VARCHAR(255) NOT NULL,
    role        VARCHAR(50)  NOT NULL,     -- e.g. procurement_head, vendor, requestor, etc.
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Roles needed (current hardcoded users as reference)

| Email | Role |
|---|---|
| admin@smart.com | procurement_head |
| vendor@smart.com | vendor |
| requestor@smart.com | requestor |
| rm@smart.com | regional_manager |
| sm@smart.com | site_manager |

### Message to commercial developer

> Both apps have `# TODO: Validate against DB users table` in their login endpoints.
> Before dev deployment we need to align on auth. Proposal:
> - Commercial owns the `users` table (migration + CRUD endpoints)
> - Proposed schema: id, email, password_hash (bcrypt), full_name, role, is_active, timestamps
> - Procurement will query it read-only at login (same pattern we use for `sites` table)
> - Both apps keep the same JWT secret so tokens stay interoperable
> - Once you create the migration and seed initial users, procurement can wire up real auth same day

---

## Pending: PDF Download Endpoints (Phase 10)

5 endpoints currently return HTTP 501:
- `GET /purchase-orders/{poNumber}/download` — material PO PDF
- `GET /purchase-orders/machinery/{poNumber}/pdf` — machinery PO PDF
- `GET /purchase-orders/machinery/{poNumber}/dc-pdf` — machinery delivery challan PDF
- `GET /purchase-orders/uniform/{poNumber}/pdf` — uniform PO PDF
- `GET /purchase-orders/uniform/{poNumber}/dc-pdf` — uniform delivery challan PDF

**Approach:** Use `reportlab` (pure Python, no system dependencies) or `weasyprint` (HTML→PDF).
`reportlab` is recommended for structured documents like POs.
Install: `pip install reportlab` and add to `requirements.txt`.

---

## Key Patterns

**ORM model:**
```python
class ProcVendor(Base):
    __tablename__ = "proc_vendors"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

**Pydantic schema:** camelCase, `model_config = {"from_attributes": True}`

**Router endpoint:**
```python
@router.post("", response_model=ApiResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role("procurement_head")),
):
    vendor = await service.create_vendor(db, data)
    return success_response(VendorResponse.model_validate(vendor).model_dump())
```
