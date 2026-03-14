# Procurement — Database Design

All tables use the `proc_` prefix to avoid collision with the commercial app tables in the shared `smarterp` PostgreSQL database.

---

## Prerequisites — Creating the Database

Before running migrations, the PostgreSQL database and user must exist.

```sql
-- Run once as postgres superuser
CREATE USER smarterp WITH PASSWORD 'smarterp_dev';
CREATE DATABASE smarterp OWNER smarterp;
GRANT ALL PRIVILEGES ON DATABASE smarterp TO smarterp;
```

Then run migrations from inside `procurement/`:
```bash
alembic upgrade head
```

---

## Entity Relationship Overview

```
proc_vendors
  └── proc_vendor_applications  (vendor_id FK)
  └── proc_products             (vendor_id FK)
      └── proc_product_price_change_requests (product_id FK, vendor_id FK)
      └── proc_indent_items     (product_id FK)
      └── proc_po_items         (product_id FK)

proc_extra_material_requests
  └── proc_indents              (extra_material_request_id FK, optional)
      └── proc_indent_items     (indent_id FK, CASCADE DELETE)
          └── proc_purchase_orders (indent_id FK)
              └── proc_po_items    (po_id FK, CASCADE DELETE)
              └── proc_grns        (po_id FK, UNIQUE — 1 GRN per PO)
                  └── proc_grn_items  (grn_id FK, CASCADE DELETE)
                  └── proc_grn_photos (grn_id FK, CASCADE DELETE)
              └── proc_invoices (via proc_invoice_po_links)

proc_invoices
  └── proc_invoice_po_links (invoice_id FK, UNIQUE per invoice+po)

proc_cash_purchases             (standalone, no FK to indents/POs)

proc_machinery_requests
  └── proc_machinery_purchase_orders (machinery_request_id FK)
      └── proc_machinery_grns         (po_number UNIQUE)

proc_uniform_requests
  └── proc_uniform_purchase_orders (uniform_request_id FK)

proc_notifications              (standalone per user_email)
proc_api_logs                   (standalone middleware log)
```

---

## Table Designs

### `proc_api_logs`
Auto-populated by `RequestLoggingMiddleware` on every API call.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | auto-generated |
| timestamp | TIMESTAMPTZ | NOT NULL, default now() | |
| method | VARCHAR(10) | NOT NULL | GET/POST/PUT/DELETE |
| path | VARCHAR(2048) | NOT NULL | includes query string |
| status_code | INTEGER | NOT NULL | HTTP response code |
| user_email | VARCHAR(255) | nullable | from JWT |
| user_role | VARCHAR(50) | nullable | from JWT |
| request_body | JSONB | nullable | JSON payloads only |
| response_body | JSONB | nullable | JSON responses only |
| duration_ms | INTEGER | NOT NULL | |
| client_ip | VARCHAR(45) | nullable | supports IPv6 |
| response_id | UUID | nullable | from ApiResponse.responseId |

**Indexes:** `timestamp`, `user_email`, `response_id`

---

### `proc_vendors`
Created by procurement_head. Represents the company-level vendor entity.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| vendor_code | VARCHAR(50) | UNIQUE NOT NULL | auto-gen: VEN-0001 |
| company_name | VARCHAR(255) | NOT NULL | |
| email | VARCHAR(255) | UNIQUE NOT NULL | login email |
| state | VARCHAR(100) | NOT NULL | |
| nature_of_business | VARCHAR(100) | NOT NULL | Manufacturing/Distribution/Services/Retail/Wholesale |
| gl_code | VARCHAR(50) | nullable | generated on approval: GL-YYYY-NNNN |
| status | VARCHAR(30) | NOT NULL, default 'INVITED' | INVITED / ACTIVE / SUSPENDED |
| invite_token | VARCHAR(255) | nullable | one-time portal link token, cleared on approval |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_vendor_applications`
The vendor's detailed onboarding form, submitted after invite.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| vendor_id | UUID | FK → proc_vendors NOT NULL | |
| name | VARCHAR(255) | NOT NULL | company name |
| name_of_owner | VARCHAR(255) | NOT NULL | |
| email | VARCHAR(255) | NOT NULL | |
| designation | VARCHAR(255) | NOT NULL | |
| category | VARCHAR(100) | NOT NULL | Material/Machinery/Uniform |
| types_of_business | VARCHAR(100) | NOT NULL | |
| address_line1 | TEXT | NOT NULL | |
| address_line2 | TEXT | nullable | |
| state | VARCHAR(100) | NOT NULL | |
| district | VARCHAR(100) | NOT NULL | |
| city | VARCHAR(100) | NOT NULL | |
| pin_code | VARCHAR(6) | NOT NULL | |
| gst_details | JSONB | NOT NULL | `[{state, gstNumber, gstCertificateUrl}]` |
| shop_establishment_url | VARCHAR(500) | nullable | MinIO path |
| pan_url | VARCHAR(500) | nullable | MinIO path |
| aadhaar_udyam_url | VARCHAR(500) | nullable | MinIO path |
| msme_certificate_url | VARCHAR(500) | nullable | MinIO path |
| cancelled_cheque_url | VARCHAR(500) | nullable | MinIO path |
| escalation_matrix_url | VARCHAR(500) | nullable | MinIO path |
| branch_office_details_url | VARCHAR(500) | nullable | MinIO path |
| board_resolution_url | VARCHAR(500) | nullable | MinIO path (companies only) |
| status | VARCHAR(30) | NOT NULL, default 'Pending' | Pending / Approved / Rejected |
| rejection_reason | TEXT | nullable | |
| submitted_at | TIMESTAMPTZ | NOT NULL | |
| reviewed_at | TIMESTAMPTZ | nullable | |
| reviewed_by | VARCHAR(255) | nullable | PH email |

---

### `proc_products`
Product catalog entry submitted by a vendor.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| product_code | VARCHAR(100) | UNIQUE NOT NULL | auto-gen: PRD-000001 |
| vendor_id | UUID | FK → proc_vendors NOT NULL | |
| product_name | VARCHAR(255) | NOT NULL | |
| category | VARCHAR(100) | NOT NULL | |
| subcategory | VARCHAR(100) | NOT NULL | |
| price | NUMERIC(12,2) | NOT NULL | vendor's base price |
| hsn_code | VARCHAR(8) | NOT NULL | exactly 8 digits |
| is_tax_exempt | BOOLEAN | NOT NULL, default false | |
| gst_rate | NUMERIC(5,2) | NOT NULL, default 0 | 0 if tax exempt |
| delivery_days | INTEGER | NOT NULL | min 1 |
| delivery_cost | NUMERIC(12,2) | NOT NULL, default 0 | |
| uom | VARCHAR(20) | NOT NULL | PCS/KG/LTR/BOX/MTR/SET |
| description | TEXT | nullable | |
| margin_percentage | NUMERIC(6,2) | nullable | set by PH; % markup over price |
| direct_margin_amount | NUMERIC(12,2) | nullable | set by PH; flat amount |
| final_price | NUMERIC(12,2) | NOT NULL | price + margin (auto-calculated) |
| status | VARCHAR(30) | NOT NULL, default 'Pending' | Pending / Approved / Rejected |
| rejection_reason | TEXT | nullable | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

**Margin calculation rule:**
- If `margin_percentage` set: `final_price = price × (1 + margin_percentage / 100)`
- If `direct_margin_amount` set: `final_price = price + direct_margin_amount`
- If neither: `final_price = price`

---

### `proc_product_price_change_requests`
Vendor requests a future price change; PH approves/rejects.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| product_id | UUID | FK → proc_products NOT NULL | |
| vendor_id | UUID | FK → proc_vendors NOT NULL | |
| new_price | NUMERIC(12,2) | NOT NULL | must be > 0 |
| wef_date | DATE | NOT NULL | must be future date |
| status | VARCHAR(30) | NOT NULL, default 'Pending' | Pending / Approved / Rejected |
| rejection_reason | TEXT | nullable | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| reviewed_at | TIMESTAMPTZ | nullable | |
| reviewed_by | VARCHAR(255) | nullable | |

---

### `proc_extra_material_requests`
Requestor asks RM for permission to raise an extra (non-monthly) indent.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| site_id | VARCHAR(100) | NOT NULL | |
| requestor_email | VARCHAR(255) | NOT NULL | |
| month_year | DATE | NOT NULL | first day of month |
| reason | TEXT | NOT NULL | |
| status | VARCHAR(30) | NOT NULL, default 'pending' | pending / approved / rejected / closed |
| rejection_reason | TEXT | nullable | |
| approved_by | VARCHAR(255) | nullable | RM email |
| created_at | TIMESTAMPTZ | NOT NULL | |
| reviewed_at | TIMESTAMPTZ | nullable | |

**Indexes:** `(site_id, month_year)`, `status`

---

### `proc_indents`
Material indent / purchase request raised by requestor.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| tracking_no | VARCHAR(50) | UNIQUE NOT NULL | IND/YYYY/NNNNN |
| requestor_email | VARCHAR(255) | NOT NULL | |
| site_id | VARCHAR(100) | NOT NULL | |
| for_month | VARCHAR(30) | NOT NULL | e.g. "October 2025" |
| is_monthly | BOOLEAN | NOT NULL | |
| category | VARCHAR(30) | NOT NULL | Regular / Extra Material |
| extra_material_request_id | UUID | FK → proc_extra_material_requests, nullable | |
| branch_gst | VARCHAR(15) | nullable | |
| request_category | VARCHAR(100) | nullable | |
| narration | TEXT | nullable | |
| total_value | NUMERIC(12,2) | NOT NULL, default 0 | sum of items |
| status | VARCHAR(40) | NOT NULL, default 'PENDING_PH_APPROVAL' | See states below |
| rejection_reason | TEXT | nullable | |
| rejected_by | VARCHAR(255) | nullable | |
| approved_by | VARCHAR(255) | nullable | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

**Status states:** `PENDING_PH_APPROVAL → PH_APPROVED → PO_CREATED`
Rejection state: `REJECTED_BY_PH`

---

### `proc_indent_items`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| indent_id | UUID | FK → proc_indents, CASCADE DELETE | |
| product_id | UUID | FK → proc_products, nullable | nullable for non-catalog items |
| product_name | VARCHAR(255) | NOT NULL | snapshot at time of indent |
| quantity | NUMERIC(10,3) | NOT NULL | |
| size | VARCHAR(50) | nullable | apparel only |
| unit_price | NUMERIC(12,2) | NOT NULL | snapshot |
| total_price | NUMERIC(12,2) | NOT NULL | quantity × unit_price |

---

### `proc_purchase_orders`
Generated by PH from an approved indent.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| po_number | VARCHAR(50) | UNIQUE NOT NULL | PO-NNNNNN |
| indent_id | UUID | FK → proc_indents, nullable | |
| vendor_id | UUID | FK → proc_vendors, nullable | |
| site_id | VARCHAR(100) | NOT NULL | |
| po_date | TIMESTAMPTZ | NOT NULL | |
| expected_delivery_date | DATE | nullable | |
| tat | INTEGER | nullable | turn-around-time days |
| tat_status | VARCHAR(20) | nullable | Within TAT / Out of TAT |
| delivery_type | VARCHAR(20) | nullable | Hand / Courier |
| courier_name | VARCHAR(100) | nullable | |
| pod_number | VARCHAR(100) | nullable | |
| status | VARCHAR(40) | NOT NULL, default 'Not Delivered' | See states below |
| date_of_delivery | DATE | nullable | |
| reason | TEXT | nullable | |
| pod_image_url | VARCHAR(500) | nullable | MinIO path |
| signed_pod_url | VARCHAR(500) | nullable | MinIO path |
| signed_dc_url | VARCHAR(500) | nullable | MinIO path |
| total_value | NUMERIC(12,2) | NOT NULL | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

**Status states:** `Not Delivered → Processing → Dispatched → Delivered`
(Vendor sets status via PUT; GRN submission automatically sets `Delivered`)

---

### `proc_po_items`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| po_id | UUID | FK → proc_purchase_orders, CASCADE DELETE | |
| item_id | VARCHAR(50) | NOT NULL | e.g. "PO-951432-0" |
| product_id | UUID | FK → proc_products, nullable | |
| product_name | VARCHAR(255) | NOT NULL | snapshot |
| quantity | NUMERIC(10,3) | NOT NULL | |
| landed_price | NUMERIC(12,2) | NOT NULL | final_price + delivery_cost |
| total_amount | NUMERIC(12,2) | NOT NULL | quantity × landed_price |

---

### `proc_grns`
Goods Received Note — submitted by requestor when goods arrive. One per PO.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| po_id | UUID | FK → proc_purchase_orders, UNIQUE | one GRN per PO |
| po_number | VARCHAR(50) | NOT NULL | denormalised for quick lookup |
| requestor_email | VARCHAR(255) | NOT NULL | |
| predefined_comment | VARCHAR(50) | nullable | e.g. "PARTIAL", "DAMAGED", "OTHER" |
| comments | TEXT | nullable | mandatory if predefined = 'OTHER' |
| signed_dc_url | VARCHAR(500) | NOT NULL | MinIO path |
| submitted_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_grn_items`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| grn_id | UUID | FK → proc_grns, CASCADE DELETE | |
| item_id | VARCHAR(50) | NOT NULL | matches po_items.item_id |
| item_name | VARCHAR(255) | NOT NULL | |
| ordered_quantity | NUMERIC(10,3) | NOT NULL | |
| received_quantity | NUMERIC(10,3) | NOT NULL | |
| is_accepted | BOOLEAN | NOT NULL | |

---

### `proc_grn_photos`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| grn_id | UUID | FK → proc_grns, CASCADE DELETE | |
| photo_url | VARCHAR(500) | NOT NULL | MinIO path |

---

### `proc_invoices`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| invoice_id | VARCHAR(50) | UNIQUE NOT NULL | INV-XXXXXX |
| vendor_id | UUID | FK → proc_vendors, nullable | |
| invoice_no | VARCHAR(100) | NOT NULL | vendor's own invoice number |
| invoice_type | VARCHAR(20) | NOT NULL | material / machinery / uniform |
| state | VARCHAR(100) | NOT NULL | billing state |
| bill_amount | NUMERIC(12,2) | NOT NULL | validated against GRN total |
| bill_url | VARCHAR(500) | NOT NULL | MinIO path |
| status | VARCHAR(30) | NOT NULL, default 'Pending' | Pending / Approved / Rejected |
| rejection_reason | TEXT | nullable | |
| submitted_at | TIMESTAMPTZ | NOT NULL | |
| reviewed_at | TIMESTAMPTZ | nullable | |
| reviewed_by | VARCHAR(255) | nullable | |

---

### `proc_invoice_po_links`
Links one invoice to one or more POs (consolidated invoices).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| invoice_id | UUID | FK → proc_invoices | |
| po_number | VARCHAR(50) | NOT NULL | |

**Unique constraint:** `(invoice_id, po_number)`

---

### `proc_cash_purchases`
Direct cash purchases by requestor (no vendor/PO flow).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| purchase_id | VARCHAR(50) | UNIQUE NOT NULL | CP-XXXXXX |
| requestor_email | VARCHAR(255) | NOT NULL | |
| site_id | VARCHAR(100) | NOT NULL | |
| for_the_month | DATE | NOT NULL | first day of month |
| vendor_name | VARCHAR(255) | nullable | ad-hoc vendor name |
| gst_no | VARCHAR(15) | nullable | |
| products | JSONB | NOT NULL | `[{productName, quantity, cost}]` |
| total_cost | NUMERIC(12,2) | NOT NULL | |
| bill_url | VARCHAR(500) | NOT NULL | MinIO path |
| status | VARCHAR(30) | NOT NULL, default 'Pending' | Pending / Approved / Rejected |
| rejection_reason | TEXT | nullable | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_machinery_requests`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| requisition_id | VARCHAR(50) | UNIQUE NOT NULL | MREQ-NNNNN |
| site_id | VARCHAR(100) | NOT NULL | |
| site_manager_email | VARCHAR(255) | NOT NULL | |
| justification | TEXT | NOT NULL | min 5 chars |
| items | JSONB | NOT NULL | `[{machineName, quantity, requestType, oldAssetId}]` |
| status | VARCHAR(40) | NOT NULL, default 'PENDING_PH_APPROVAL' | PENDING_PH_APPROVAL / PROCESSED / REJECTED |
| rejection_reason | TEXT | nullable | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_machinery_purchase_orders`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| po_number | VARCHAR(50) | UNIQUE NOT NULL | PO-MAC-NNNNN |
| machinery_request_id | UUID | FK → proc_machinery_requests, nullable | |
| vendor_id | UUID | FK → proc_vendors, nullable | |
| site_id | VARCHAR(100) | NOT NULL | |
| region | VARCHAR(100) | nullable | |
| po_date | TIMESTAMPTZ | NOT NULL | |
| expected_delivery_date | DATE | nullable | |
| tat | INTEGER | nullable | |
| tat_status | VARCHAR(20) | nullable | |
| delivery_type | VARCHAR(20) | nullable | |
| courier_name | VARCHAR(100) | nullable | |
| pod_number | VARCHAR(100) | nullable | |
| status | VARCHAR(40) | NOT NULL, default 'Not Delivered' | same states as proc_purchase_orders |
| date_of_delivery | DATE | nullable | |
| reason | TEXT | nullable | |
| pod_image_url / signed_pod_url / signed_dc_url | VARCHAR(500) | nullable | MinIO paths |
| items | JSONB | NOT NULL | `[{productName, quantity, landedPrice}]` |
| created_at / updated_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_machinery_grns`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| po_number | VARCHAR(50) | UNIQUE NOT NULL | |
| requestor_email | VARCHAR(255) | NOT NULL | |
| comments | TEXT | nullable | |
| signed_dc_url | VARCHAR(500) | NOT NULL | MinIO path |
| asset_condition_proof_url | VARCHAR(500) | NOT NULL | mandatory for machinery |
| packaging_images | JSONB | nullable | array of MinIO URLs |
| submitted_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_uniform_requests`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| request_id | VARCHAR(50) | UNIQUE NOT NULL | UNF-NNNNN |
| employee_code | VARCHAR(50) | NOT NULL | |
| employee_name | VARCHAR(255) | NOT NULL | |
| designation | VARCHAR(100) | NOT NULL | |
| site | VARCHAR(100) | NOT NULL | |
| client | VARCHAR(100) | nullable | |
| issue_type | VARCHAR(20) | NOT NULL | new / replacement / backfill |
| replacing_employee_code | VARCHAR(50) | nullable | |
| justification | TEXT | nullable | |
| is_early_replacement | BOOLEAN | NOT NULL, default false | |
| items | JSONB | NOT NULL | `[{itemName, size, quantity}]` |
| status | VARCHAR(40) | NOT NULL, default 'PENDING_PH_APPROVAL' | |
| rejection_reason | TEXT | nullable | |
| created_at / updated_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_uniform_purchase_orders`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| po_number | VARCHAR(50) | UNIQUE NOT NULL | PO-UNF-NNNNN |
| uniform_request_id | UUID | FK → proc_uniform_requests, nullable | |
| vendor_id | UUID | FK → proc_vendors, nullable | |
| employee_name / employee_code | VARCHAR | NOT NULL | |
| site_name | VARCHAR(255) | NOT NULL | |
| region | VARCHAR(100) | nullable | |
| po_date | TIMESTAMPTZ | NOT NULL | |
| expected_delivery_date | DATE | nullable | |
| tat / tat_status / delivery_type / courier_name / pod_number | various | nullable | |
| status | VARCHAR(40) | NOT NULL, default 'Not Delivered' | same states as material PO |
| date_of_delivery | DATE | nullable | |
| pod_image_url / signed_pod_url / signed_dc_url | VARCHAR(500) | nullable | MinIO paths |
| items | JSONB | NOT NULL | `[{productName, size, quantity, landedPrice}]` |
| created_at / updated_at | TIMESTAMPTZ | NOT NULL | |

---

### `proc_notifications`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | UUID | PK | |
| user_email | VARCHAR(255) | NOT NULL | recipient |
| title | VARCHAR(255) | NOT NULL | |
| message | TEXT | NOT NULL | |
| is_read | BOOLEAN | NOT NULL, default false | |
| link | VARCHAR(500) | nullable | frontend nav path |
| created_at | TIMESTAMPTZ | NOT NULL | |

**Indexes:** `user_email`, `is_read`

---

## Migration Commands

```bash
# Run all migrations (from inside procurement/)
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check current version
alembic current

# Generate new migration (after model changes)
alembic revision --autogenerate -m "description"
```
