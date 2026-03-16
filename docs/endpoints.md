# Procurement — API Endpoints Tracker

**Base URL (local):** `http://localhost:8001`
**Docs:** `http://localhost:8001/procurement/docs`

**Status legend:**
- ✅ Implemented — fully working
- 🔧 Stub — route exists, returns 500 NotImplementedError
- 📋 Planned — not yet started

**Test legend:**
- ✅ Tested — passed in manual testing
- ⚠️ Issue — known problem (see notes)
- — Not yet tested

---

## Auth

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/auth/login | public | ✅ | ✅ | Hardcoded credentials (5 dev users) |

---

## Vendors

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/vendors | procurement_head | ✅ | ✅ | Creates vendor, auto-generates VEN-NNNN code + invite_token |
| GET | /api/procurement/vendors/category/{category} | procurement_head | ✅ | ⚠️ | Filters ACTIVE vendors by category. **Known issue: returns 404 when server runs with `--reload`. Works correctly with `python run.py` (no reload).** |

## Vendor Applications

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/vendor-applications | vendor | ✅ | ✅ | Vendor submits onboarding form; doc files as URLs (pre-upload to MinIO) |
| GET | /api/procurement/vendor-applications | procurement_head | ✅ | ✅ | Optional `?status=` filter (Pending/Approved/Rejected) |
| GET | /api/procurement/vendor-applications/{vendorId} | procurement_head | ✅ | ✅ | Latest application for that vendor |
| POST | /api/procurement/vendor-applications/approve | procurement_head | ✅ | ✅ | Body: `{vendorId}`. Sets vendor ACTIVE, generates GL code |
| POST | /api/procurement/vendor-applications/{vendorId}/reject | procurement_head | ✅ | ✅ | Body: `{rejectionReason}` |

---

## Products

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/products | any auth | ✅ | ✅ | Body includes `vendorCode`. Auto-generates PRD0000001 code. PK is product_code (no UUID) |
| GET | /api/procurement/products | any auth | ✅ | ✅ | `?status=&search=&page=1&limit=10`. Response: `{pagination, products}` |
| POST | /api/procurement/products/approve | any auth | ✅ | ✅ | Body: `{productIds: ["PRD0000001"]}` (product codes, not UUIDs) |
| POST | /api/procurement/products/{productCode}/reject | any auth | ✅ | ✅ | Body: `{reason}` (not rejectionReason) |
| GET | /api/procurement/products/catalog | any auth | ✅ | ✅ | Only Approved products |
| GET | /api/procurement/vendor/products | any auth | ✅ | ✅ | `?vendor_code=VEN0000001` |
| DELETE | /api/procurement/products/{productCode} | any auth | ✅ | ✅ | `?vendor_code=VEN0000001` |
| GET | /api/procurement/products/bulk-upload-template | any auth | ✅ | ✅ | Excel template download |
| POST | /api/procurement/products/bulk-upload | any auth | ✅ | ✅ | `?vendor_code=VEN0000001`. Upload Excel to batch create products |
| POST | /api/procurement/products/price-change-requests | any auth | ✅ | ✅ | Body: `{productCode, vendorCode, newPrice, wefDate}` |
| GET | /api/procurement/products/price-change-requests | any auth | ✅ | ✅ | List all pending requests |
| POST | /api/procurement/products/price-change-requests/approve | any auth | ✅ | ✅ | Body: `{approvalId: 1}` (int, not UUID) |
| POST | /api/procurement/products/price-change-requests/{approvalId}/reject | any auth | ✅ | ✅ | Body: `{reason}` (not rejectionReason). approvalId is int |
| GET | /api/procurement/products/margins | procurement_head | ✅ | ✅ | All approved products with margin info |
| GET | /api/procurement/products/margins/export-template | procurement_head | ✅ | ✅ | Excel template for bulk margin upload |
| POST | /api/procurement/products/margins/bulk-upload | procurement_head | ✅ | ✅ | Upload Excel to set margins in bulk |

---

## Sites

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| GET | /api/procurement/user-sites | any auth | ✅ | ✅ | Returns all sites (no user-site assignment table yet) |
| GET | /api/procurement/sites/{siteId}/material-catalog | any auth | ✅ | ✅ | All Approved products from proc_products (not site-specific yet) |
| GET | /api/procurement/sites/{siteId}/history | any auth | ✅ | ✅ | Indent history for site (spec #8.6). `?month=2025-09`. Response: `[{siteId, trackingNo, requestDate, siteBudget, value, status, balance}]` |
| GET | /api/procurement/sites/{siteId}/indent-history | any auth | ✅ | ✅ | Indents for site from proc_indents |
| GET | /api/procurement/sites/options | any auth | ✅ | ✅ | Dropdown: `{siteId, siteName, city, state}` from commercial `sites` table |

---

## Extra Material Requests

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| GET | /api/procurement/extra-material-requests/status | requestor | ✅ | ✅ | Query param: `?siteId=`. Returns `hasApproval` + `requestId` |
| POST | /api/procurement/extra-material-requests | requestor | ✅ | ✅ | `monthYear`: "YYYY-MM" format. One per requestor+site+month |
| GET | /api/procurement/extra-material-requests | regional_manager | ✅ | ✅ | Optional `?status=` filter (pending/approved/rejected) |
| POST | /api/procurement/extra-material-requests/approve | regional_manager | ✅ | ✅ | Body: `{requestId}` |
| POST | /api/procurement/extra-material-requests/{requestId}/reject | regional_manager | ✅ | ✅ | Body: `{rejectionReason}` |

---

## Indents

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/indents | any auth | ✅ | ✅ | Body: `{requestorEmail, siteId, forMonth, isMonthly, category, items[{productCode, quantity}]}`. Prices looked up from DB. Tracking: `IND/YYYY/NNNNN`. Regular→PENDING_PH_APPROVAL, Extra Material→PENDING_RM_APPROVAL (closes EMR). Response: `{message, trackingNo, status}` |
| GET | /api/procurement/indents | any auth | ✅ | ✅ | `?status=&search=&page=1&limit=10`. Response: `{pagination, indents}` with IndentListItem schema |
| GET | /api/procurement/indents/my-indents | any auth | ✅ | ✅ | `?requestor_email=` (not from JWT) |
| POST | /api/procurement/indents/approve | any auth | ✅ | ✅ | Body: `{indentIds: ["IND/2026/00001"]}` (bulk, trackingNos). RM→PENDING_PH, PH→PO_CREATED (auto-creates POs grouped by vendor). Response includes `poNumbers` |
| GET | /api/procurement/indents/{trackingNo} | any auth | ✅ | ✅ | Path param is trackingNo (slashes OK via :path). Rich detail with products, totals, tax |
| PUT | /api/procurement/indents/{trackingNo} | any auth | ✅ | ✅ | Body: `{branchGst, requestCategory, narration, products[{productCode, quantity}]}`. Only allowed in PENDING_PH/RM_APPROVAL. Returns full detail. |
| POST | /api/procurement/indents/reject | any auth | ✅ | ✅ | Body: `{trackingNo, reason}` (trackingNo in body because slashes in URL). Sets REJECTED_BY_PH or REJECTED_BY_RM |

---

## Purchase Orders (Material)

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| GET | /api/procurement/purchase-orders | any auth | ✅ | ✅ | `?search=&page=1&limit=10`. Response includes dcNumber, dcDate, signedDcISmartUrl (PH view fields) |
| GET | /api/procurement/purchase-orders/export | any auth | ✅ | ✅ | `?search=` optional filter. Excel export matches list view filtering |
| GET | /api/procurement/purchase-orders/{poNumber}/download | any auth | ✅ | — | `?type=po_pdf|po_excel|dc_pdf`. `po_excel` implemented; `po_pdf`/`dc_pdf` return 501 (needs PDF library) |
| PUT | /api/procurement/purchase-orders/{poNumber} | any auth | ✅ | — | **multipart/form-data**: `data` JSON (deliveryType, courierName, podNumber, status, dateOfDelivery, reason) + files (podImage, signedPod, signedDc). Delivered requires all files+fields. Courier requires courierName. Out-of-TAT requires reason |
| POST | /api/procurement/purchase-orders/{poNumber}/grn | any auth | ✅ | — | **multipart/form-data**: `data` JSON (items, predefinedComment, comments, requestorEmail) + signedDc (required) + photos (up to 2). Sets PO → `GRN_SUBMITTED`. Backend looks up item names/ordered qty from PO items |

---

## Invoices (Material)

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/invoices | any auth | ✅ | ✅ | Body: `{invoiceNo, invoiceType, state, billAmount, billUrl, poNumbers[]}`. Auto-generates `INV-NNNNNN`. Sets linked POs → `INVOICE_SUBMITTED` |
| GET | /api/procurement/invoices | any auth | ✅ | ✅ | Optional `?status=` filter (Pending/Approved/Rejected) |
| POST | /api/procurement/invoices/approve | any auth | ✅ | ✅ | Body: `{invoiceId}` (UUID) |
| POST | /api/procurement/invoices/{invoiceId}/reject | any auth | ✅ | ✅ | Path: UUID. Body: `{rejectionReason}` |

---

## Cash Purchases

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| POST | /api/procurement/cash-purchases | any auth | ✅ | ✅ | Body: `{siteId, forTheMonth (YYYY-MM), vendorName?, gstNo?, products[], totalCost, billUrl}`. Auto-generates `CP-NNNNNN` |
| GET | /api/procurement/cash-purchases | any auth | ✅ | ✅ | Optional `?status=` filter (Pending/Approved/Rejected) |
| POST | /api/procurement/cash-purchases/approve | any auth | ✅ | ✅ | Body: `{purchaseId}` (UUID) |
| POST | /api/procurement/cash-purchases/{purchaseId}/reject | any auth | ✅ | ✅ | Path: UUID. Body: `{rejectionReason}` |

---

## Machinery

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| GET | /api/procurement/machinery/options | any auth | ✅ | ✅ | Returns static list of 17 machinery types |
| POST | /api/procurement/machinery-requests | any auth | ✅ | ✅ | Auto-generates `MREQ-NNNNN`. Body: `{siteId, justification, items[]}` |
| GET | /api/procurement/machinery-requests | any auth | ✅ | ✅ | Optional `?status=` filter |
| GET | /api/procurement/machinery-requests/{requestId}/details-for-approval | any auth | ✅ | ✅ | |
| POST | /api/procurement/machinery-requests/{requestId}/fulfill | any auth | ✅ | ✅ | Creates `PO-MAC-NNNNN`. Sets request → `PROCESSED` |
| POST | /api/procurement/machinery-requests/{requestId}/reject | any auth | ✅ | ✅ | Body: `{rejectionReason}`. Sets → `REJECTED` |
| GET | /api/procurement/vendor/machinery-orders | any auth | ✅ | ✅ | All machinery POs |
| GET | /api/procurement/purchase-orders/machinery/{poNumber} | any auth | ✅ | ✅ | |
| PUT | /api/procurement/purchase-orders/machinery/{poNumber} | any auth | ✅ | ✅ | Update delivery status + courier details |
| GET | /api/procurement/purchase-orders/machinery/{poNumber}/pdf | any auth | 🔧 | — | stub — 501 Not Implemented |
| GET | /api/procurement/purchase-orders/machinery/{poNumber}/dc-pdf | any auth | 🔧 | — | stub — 501 Not Implemented |
| GET | /api/procurement/purchase-orders/machinery/{poNumber}/export | any auth | ✅ | ✅ | Excel export of single PO |
| GET | /api/procurement/vendor/machinery-orders/export-all | any auth | ✅ | ✅ | Excel export of all machinery POs |
| GET | /api/procurement/requestor/machinery-orders | any auth | ✅ | ✅ | |
| POST | /api/procurement/purchase-orders/machinery/{poNumber}/grn | any auth | ✅ | ✅ | Body: `{signedDcUrl, assetConditionProofUrl, packagingImages[], comments?}` |
| GET | /api/procurement/requestor/machinery-orders/export | any auth | ✅ | ✅ | Excel export |
| POST | /api/procurement/purchase-orders/machinery/consolidated-items | any auth | ✅ | ✅ | Body: `{poNumbers[]}`. Returns merged items list |
| POST | /api/procurement/invoices/consolidated/machinery | any auth | ✅ | ✅ | Submit machinery invoice. Auto-generates `INV-NNNNNN`. Sets POs → `INVOICE_SUBMITTED` |
| GET | /api/procurement/invoices/machinery/approval-list | any auth | ✅ | ✅ | Machinery invoices pending approval |
| POST | /api/procurement/invoices/machinery/approve | any auth | ✅ | ✅ | Body: `{invoiceId}` (UUID) |
| POST | /api/procurement/invoices/machinery/{invoiceId}/reject | any auth | ✅ | ✅ | Path: UUID. Body: `{rejectionReason}` |
| GET | /api/procurement/machinery/grn/{poNumber}/evidence | any auth | ✅ | ✅ | Returns GRN photos + condition proof |

---

## Uniforms

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| GET | /api/procurement/employees/uniform-search | any auth | ✅ | ✅ | `?q=` search param. Returns mock employee data |
| GET | /api/procurement/uniforms/configuration | any auth | ✅ | ✅ | Returns 10 uniform item types with sizes |
| POST | /api/procurement/uniform-requests | any auth | ✅ | ✅ | Auto-generates `UNF-NNNNN` |
| GET | /api/procurement/uniform-requests | any auth | ✅ | ✅ | Optional `?status=` filter |
| GET | /api/procurement/employees/{employeeCode}/uniform-history | any auth | ✅ | ✅ | All requests for that employee |
| POST | /api/procurement/uniform-requests/{requestId}/fulfill | any auth | ✅ | ✅ | Creates `PO-UNF-NNNNN`. Sets request → `PROCESSED` |
| POST | /api/procurement/uniform-requests/{requestId}/reject | any auth | ✅ | ✅ | Body: `{rejectionReason}`. Sets → `REJECTED` |
| GET | /api/procurement/purchase-orders/uniform | any auth | ✅ | ✅ | All uniform POs |
| GET | /api/procurement/purchase-orders/uniform/{poNumber} | any auth | ✅ | ✅ | |
| PUT | /api/procurement/purchase-orders/uniform/{poNumber} | any auth | ✅ | ✅ | Update delivery status + courier details |
| GET | /api/procurement/purchase-orders/uniform/{poNumber}/pdf | any auth | 🔧 | — | stub — 501 Not Implemented |
| GET | /api/procurement/purchase-orders/uniform/{poNumber}/dc-pdf | any auth | 🔧 | — | stub — 501 Not Implemented |
| GET | /api/procurement/purchase-orders/uniform/{poNumber}/export | any auth | ✅ | ✅ | Excel export of single PO |
| GET | /api/procurement/purchase-orders/uniform/export-all | any auth | ✅ | ✅ | Excel export of all uniform POs |
| GET | /api/procurement/requestor/uniform-orders | any auth | ✅ | ✅ | |
| POST | /api/procurement/purchase-orders/uniform/{poNumber}/grn | any auth | ✅ | ✅ | Body: `{signedDcUrl, comments?}`. Sets PO → `Delivered` |
| GET | /api/procurement/requestor/uniform-orders/export | any auth | ✅ | ✅ | Excel export |
| POST | /api/procurement/purchase-orders/uniform/consolidated-items | any auth | ✅ | ✅ | Body: `{poNumbers[]}`. Returns merged items list |
| POST | /api/procurement/invoices/consolidated | any auth | ✅ | ✅ | Submit uniform invoice. Auto-generates `INV-NNNNNN`. Sets POs → `INVOICE_SUBMITTED` |

---

## Notifications

| Method | Path | Role | Status | Test | Notes |
|---|---|---|---|---|---|
| GET | /api/procurement/notifications | any auth | ✅ | ✅ | List notifications for logged-in user (filtered by JWT email) |
| POST | /api/procurement/notifications/mark-as-read | any auth | ✅ | ✅ | Body: `{ids: [UUID]}`. Returns `{marked: N}` |

---

## Summary

| Phase | Endpoints | Implemented | Stubs | Tested | % Done |
|---|---|---|---|---|---|
| Phase 1 — Skeleton | 1 | 1 (login) | 0 | ✅ 1 | 100% |
| Phase 2 — Vendors & Products | 22 | 22 | 0 | ✅ 21 / ⚠️ 1 | 100% |
| Phase 3 — Indents & EMR | 12 | 12 | 0 | ✅ 12 | 100% |
| Phase 4 — POs & GRN | 6 | 5 | 1 | ✅ 5 | 83% |
| Phase 5 — Invoices & Cash | 8 | 8 | 0 | ✅ 8 | 100% |
| Phase 6 — Machinery | 22 | 20 | 2 | ✅ 20 | 91% |
| Phase 7 — Uniforms | 19 | 17 | 2 | ✅ 17 | 89% |
| Phase 8 — Notifications | 2 | 2 | 0 | ✅ 2 | 100% |
| Sites | 5 | 5 | 0 | ✅ 5 | 100% |
| **Total** | **97** | **92** | **5** | **91 ✅ / 1 ⚠️** | **95%** |

---

## Known Issues

| Endpoint | Issue | Workaround |
|---|---|---|
| `GET /vendors/category/{category}` | Returns 404 when server runs with `uvicorn --reload` (watchfiles serves stale code in subprocess) | Run server with `python run.py` (no reload). Route works correctly. |
