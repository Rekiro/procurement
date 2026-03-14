# API Specification: Create New Vendor

This API is called when add vendor form is submitted

1. Endpoint: POST /api/vendors

2. Authorization:

- This endpoint must be protected.
- Access is restricted to users with the Procurement Head role.

3. Request Body:  
A JSON object with the following structure:

|   |   |   |
|---|---|---|
|**Field Name**|**Data Type**|**Required**|
|vendorName|String|Yes|
|state|String|Yes|
|emailId|String|Yes|
|natureOfBusiness|String|Yes|

4. Example JSON Payload:

```json
{
    "vendorName": "Global Tech Innovations",
    "state": "Karnataka",
    "emailId": "info@globaltech.com",
    "natureOfBusiness": "Services"
}
```

5. Allowed Values for Validation:

- state: Must be one of ["Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Uttar Pradesh", "Gujarat", "Rajasthan"]
- natureOfBusiness: Must be one of ["Manufacturing", "Distribution", "Services", "Retail", "Wholesale"]

An invite email should be sent to the vendor’s email id with login credentials and link to log into the system

# API Specification: Create Vendor Application

This API is called when vendor fills the 4 step registration form

1. Endpoint & Authorization

- Endpoint: POST /api/vendor-applications
- Authorization: Requires Vendor role.
- Request Format: multipart/form-data

2. Request Payload

The request must contain a data field with a JSON string and separate fields for each file upload.

A. data (JSON String)

Contains all text-based information. Key validations are noted below.

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Validation Notes**|
|name|String|Yes|Min 2 characters|
|nameOfOwner|String|Yes|Min 2 characters|
|email|String|Yes|Must be a valid email|
|designation|String|Yes|Min 2 characters|
|category|String|Yes|Must be one of the predefined options|
|typesOfBusiness|String|Yes|Must be one of the predefined options|
|addressLine1|String|Yes|Min 5 characters|
|addressLine2|String|No||
|state|String|Yes|Must be one of the predefined options|
|district|String|Yes||
|city|String|Yes||
|pinCode|String|Yes|Must be exactly 6 digits|
|gstDetails|Array of Objects|Yes|Must contain at least one GST entry|

gstDetails Object Structure:

- state: (String) Required.
- gstNumber: (String) Required, must match GSTIN format.
- gstCertificate: (String) Required, must contain the field name of the corresponding uploaded file.

B. File Parts (Binary Data)

Each file is a separate part in the form data.

- Validation for all files: Max size 1MB. Allowed types: PDF, JPEG, PNG.

|   |   |
|---|---|
|**Field Name**|**Required**|
|shopAndEstablishmentNo|Yes|
|panNo|Yes|
|gstCertificate files|Yes (for each GST entry)|
|aadhaarOrUdyamCopy|Yes|
|msmeCertificate|Yes|
|cancelledCheque|Yes|
|escalationMatrix|Yes|
|branchOfficeDetails|Yes|
|boardResolution|Conditional*|

_*boardResolution is required if typesOfBusiness is "Private Limited" or "LLP"._

_After submission vendor code (eg. VEN1234) and GL code (eg. GL1234) should be created._

# API Specification: Vendor Application Approval

This details the APIs required for the Procurement Head's vendor approval dashboard. This interface is used to review and action the multi-step registration forms submitted by vendors.

**1. API to Fetch Vendor Applications (List View)**

This API populates the main table with all vendor applications, supporting filtering and pagination.

- **Endpoint:** GET /api/vendor-applications
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - status (string, optional): Filters by status (e.g., "Pending", "Approved", "Rejected").
    - search (string, optional): Filters by vendor name, category, or email.
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination details and an array of vendor summaries.

```json
{
    "pagination": {
        "currentPage": 1,
        "totalPages": 10,
        "totalItems": 98
    },
    "vendors": [
        {
            "id": 101,
            "name": "Global Tech Innovations",
            "category": "Services",
            "nameOfOwner": "Anil Kumar",
            "email": "info@globaltech.com",
            "status": "Pending"
        }
    ]
}
```

**2. API to Fetch Full Vendor Details**

This API is called when the Procurement Head clicks a vendor's name to view their full application.

- Endpoint: GET /api/vendor-applications/{vendorId}
- Authorization: Procurement Head role required.
- URL Parameter:
    - {vendorId} (number, required): The unique ID of the vendor application.

Success Response (200 OK)

A single JSON object containing the complete and unabridged details of the vendor's application.

```json
{
    "id": 101,
    "name": "Global Tech Innovations",
    "nameOfOwner": "Anil Kumar",
    "email": "info@globaltech.com",
    "designation": "CEO",
    "category": "Services",
    "typesOfBusiness": "Private Limited",
    "shopAndEstablishmentNoUrl": "https://storage.cloud.com/vendor-docs/101/shop-establishment-cert.pdf",
    "panNoUrl": "https://storage.cloud.com/vendor-docs/101/pan-card.pdf",
    "addressLine1": "123 Tech Park, Silicon Valley Layout",
    "addressLine2": "Electronic City, Phase 1",
    "state": "Karnataka",
    "district": "Bengaluru Urban",
    "city": "Bengaluru",
    "pinCode": "560100",
    "gstDetails": [
        {
            "state": "Karnataka",
            "gstNumber": "29ABCDE1234F1Z5",
            "gstCertificateUrl": "https://storage.cloud.com/vendor-docs/101/gst-cert-ka.pdf"
        },
        {
            "state": "Maharashtra",
            "gstNumber": "27PQRST6789G1Z2",
            "gstCertificateUrl": "https://storage.cloud.com/vendor-docs/101/gst-cert-mh.pdf"
        }
    ],
    "aadhaarOrUdyamCopyUrl": "https://storage.cloud.com/vendor-docs/101/udyam-registration.pdf",
    "msmeCertificateUrl": "https://storage.cloud.com/vendor-docs/101/msme-cert.pdf",
    "boardResolutionUrl": "https://storage.cloud.com/vendor-docs/101/board-resolution.pdf",
    "cancelledChequeUrl": "https://storage.cloud.com/vendor-docs/101/cancelled-cheque.jpg",
    "escalationMatrixUrl": "https://storage.cloud.com/vendor-docs/101/escalation-matrix.pdf",
    "branchOfficeDetailsUrl": "https://storage.cloud.com/vendor-docs/101/branch-details.pdf",
    "status": "Pending"
}
```

**3. API to Approve Vendor Applications**

This endpoint handles both single and bulk vendor approvals.

- Endpoint: POST /api/vendor-applications/approve
- Authorization: Procurement Head role required.

Request Body (JSON)

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|vendorIds|Array of Numbers|Yes|An array containing one or more ids of vendors to be approved.|

**Example Payload**

```json
{
    "vendorIds": [
        101,
        102
    ]
}
```

**4. API to Reject a Vendor Application**

This endpoint is used to reject a single vendor's application.

- Endpoint: POST /api/vendor-applications/{vendorId}/reject
- Authorization: Procurement Head role required.
- URL Parameter:
    - {vendorId} (number, required): The id of the vendor application to reject.

**Request Body (JSON)**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|reason|String|Yes|A comment detailing why the application was rejected.|

**Example Payload**

```json
{
    "reason": "PAN card document is not clear. Please re-upload."
}
```

# 4. API Specification: Submit New Product for Approval

This API is called when vendor submits the upload product form

**1. Endpoint & Authorization**

- **Endpoint:** POST /api/products
- **Authorization:** Requires **Vendor** role. (The vendor ID will be inferred from the authenticated user).

**2. Request Body**

The API will accept a JSON object with the following structure.

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Validation Notes**|
|productName|String|Yes|Min 2 characters.|
|category|String|Yes|Must be one of the predefined options.|
|subcategory|String|Yes|Must be one of the predefined options.|
|price|Number|Yes|Must be greater than 0.|
|hsnCode|String|Yes|Must be exactly 8 digits.|
|isTaxExempt|Boolean|Yes|Default is false.|
|gstRate|Number|Yes|Must be <br><br> 0 (allows 0 if isTaxExempt is true).|
|deliveryDays|Number|Yes|Minimum 1 day.|
|deliveryCost|Number|Yes|Minimum 0.|
|uom|String|Yes|Unit of Measurement (e.g., "PCS", "KG").|
|description|String|No|Optional product description.|

**3. Example JSON Payload**

```json
{
    "productName": "Premium Cleaning Liquid",
    "category": "Regular",
    "subcategory": "Cleaning Chemicals",
    "price": 450.50,
    "hsnCode": "34029010",
    "isTaxExempt": false,
    "gstRate": 18,
    "deliveryDays": 3,
    "deliveryCost": 50,
    "uom": "LTR",
    "description": "5L canister of all-purpose cleaning liquid."
}
```

# 5. API Specification: Product Approval

This details the APIs required for the Procurement Head's product approval dashboard. This interface is used to review and action new products submitted by vendors.

**1. API to Fetch Products for Approval (List View)**

This API populates the main table with all product submissions, supporting filtering and pagination.

- **Endpoint:** GET /api/products
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - status (string, optional): Filters by status (e.g., "Pending", "Approved").
    - search (string, optional): Filters by product name.
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination details and an array of product objects matching the Product interface.

```json
{
    "pagination": {
        "currentPage": 1,
        "totalPages": 8,
        "totalItems": 75
    },
    "products": [
        {
            "id": 101,
            "productName": "Industrial Strength Floor Cleaner",
            "vendor": "Global Supplies Co.",
            "category": "Regular",
            "subcategory": "Cleaning Chemicals",
            "price": 1250.75,
            "hsnCode": "34021100",
            "isTaxExempt": false,
            "gstRate": 18,
            "uom": "LTR",
            "deliveryDays": 5,
            "costOfDelivery": 250,
            "description": "Concentrated floor cleaner for heavy-duty use.",
            "status": "Pending"
        },
        {
            "id": 102,
            "productName": "Organic Vegetables - Bulk",
            "vendor": "Fresh Farms Ltd.",
            "category": "Human Consumables",
            "subcategory": "Vegetables",
            "price": 80.00,
            "hsnCode": "07099900",
            "isTaxExempt": true,
            "gstRate": 0,
            "uom": "KG",
            "deliveryDays": 1,
            "costOfDelivery": 20,
            "description": "Assorted organic green vegetables.",
            "status": "Pending"
        }
    ]
}
```

**2. API to Approve Products**

This endpoint handles both single and bulk product approvals, mirroring the UI functionality.

- **Endpoint:** POST /api/products/approve
- **Authorization:** **Procurement Head** role required.

**Request Body (JSON)**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|productIds|Array of Numbers|Yes|An array containing one or more ids of products to be approved.|

**Example Payload**

```json
{
    "productIds": [
        101,
        102
    ]
}
```

**3. API to Reject a Product**

This endpoint is used to reject a single product submission, requiring a mandatory reason for the action.

- **Endpoint:** POST /api/products/{productId}/reject
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:**
    - {productId} (number, required): The id of the product to reject.

**Request Body (JSON)**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|reason|String|Yes|A comment explaining why the product was rejected.|

**Example Payload**

```json
{
    "reason": "The price is significantly higher than market rate. Please review."
}
```

# 6. API Specification: Material Order Page Data

This specifies the APIs needed for the Requestor's material ordering page, using the precise data structures and examples provided.

### **1. API to Fetch User's Assigned Sites**

This first call populates the site selection dropdown.

- **Endpoint:** GET /api/user-sites
- **Authorization:** **Requestor** role required.
- **Action:** Returns a list of sites the user is assigned to.
- **Success Response (200 OK):**

```json
[
    {
        "siteId": "siteA",
        "siteName": "Site A"
    },
    {
        "siteId": "siteB",
        "siteName": "Site B"
    }
]
```

### **2. API to Fetch Site Catalog and Details**

Called after a site is selected, this API provides the site's budget, filter options, and the specific product catalog available for that site.

***Human Consumables not to be included in budget unless some exception.**

- **Endpoint:** GET /api/sites/{siteId}/material-catalog
- **Authorization:** **Requestor** role required.
- **URL Parameter:**
    - {siteId} (string, required): The ID of the selected site (e.g., "siteB").

#### **Success Response (200 OK)**

A JSON object where the products array contains objects matching the provided Product interface exactly.

```json
{
    "siteDetails": {
        "siteId": "siteB",
        "siteName": "Site B",
        "budget": 50000.00,
        "balance": 45250.00
    },
    "filterOptions": {
        "categories": [
            {
                "value": "Fragrance",
                "label": "Fragrance"
            },
            {
                "value": "Soap - Liquid",
                "label": "Soap - Liquid"
            }
        ],
        "brands": [
            {
                "value": "LOCAL",
                "label": "LOCAL"
            },
            {
                "value": "HUL",
                "label": "HUL"
            }
        ]
    },
    "products": [
        {
            "periodFrom": "22-Oct-24",
            "vendorName": "MOPSHOP DISTRIBUTION PRIVATE LIMITED",
            "productCode": "P03386",
            "productName": "AIR DIFISUER MACHINE LOCAL - MS",
            "landedPrice": 1740,
            "manufacturedBy": "LOCAL",
            "brandName": "LOCAL",
            "hsnCode": "3925",
            "packaging": "NOS",
            "usedFor": "General",
            "category": "Fragrance",
            "lifeCycleDays": 365,
            "costOfTransportationPerKM": 3,
            "orderLeadTimeDays": 10,
            "deliveryBy": "Direct to site by Vendor - Delivery per km",
            "netProductCostPerDay": 4.77,
            "gstSetOffAvailable": true,
            "financeTreatment": "Depriciate"
        },
        {
            "periodFrom": "22-Oct-24",
            "vendorName": "MOPSHOP DISTRIBUTION PRIVATE LIMITED",
            "productCode": "P03387",
            "productName": "ALA BLEACH / RIN ALA (500 ML)HUL - MS",
            "landedPrice": 94.8,
            "manufacturedBy": "HUL",
            "brandName": "HUL",
            "hsnCode": "3402",
            "packaging": "NOS",
            "usedFor": "",
            "category": "Soap - Liquid",
            "lifeCycleDays": 30,
            "costOfTransportationPerKM": 3,
            "orderLeadTimeDays": 10,
            "deliveryBy": "Direct to site by Vendor - Delivery per km",
            "netProductCostPerDay": 3.16,
            "gstSetOffAvailable": true,
            "financeTreatment": "Depriciate"
        }
    ]
}
```

# 7. API Specification: Create Material Indent

 This API is called when a Requestor forwards their cart for approval. It creates a formal indent in the system, subject to strict backend validations, after successful submission a tracking id will be displayed to user.

### **1. Endpoint & Authorization**

- **Endpoint:** POST /api/indents
- **Authorization:** **Requestor** role required.

### **2. Request Body (JSON)**

The frontend will send a JSON object detailing the cart submission.

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|siteId|String|Yes|The unique identifier for the site the indent belongs to.|
|forMonth|String|Yes|The month and year of the request (e.g., "October 2025").|
|isMonthly|Boolean|Yes|true for recurring monthly orders. Must be false for Extra Material.|
|category|String|Yes|Must be either "Regular" or "Extra Material".|
|items|Array of Objects|Yes|The list of products being requested.|
|extraMaterialRequestId|String|Conditional|Required only if category is "Extra Material". This is the unique ID of the approved permission request.|

#### **items Object Structure:**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|productCode|String|Yes|The unique code of the product.|
|quantity|Number|Yes|The quantity requested. Must be > 0.|
|size|String|No|The specific size (for apparel only).|

  

**3. Critical Backend Logic & Workflow**

The backend must use the category field to trigger one of two distinct workflows.

**If category is "Regular":**

1. **Validation:**
    - **Single Site Cohesion:** Verify that all products in the items array belong to the specified siteId.
    - **Budget Check (with Exclusions):** Calculate the indent's total value, **excluding** any products classified as "Human Consumables". The final total must not exceed the budget for the given siteId.
2. **Routing:** If validation passes, create the indent with an initial status of PENDING_PH_APPROVAL.

**If category is "Extra Material":**

1. **Validation:**
    - **NO BUDGET CHECK** is performed for extra material indents.
    - **Authorization Check:** Verify that the extraMaterialRequestId field is present and not empty.
    - Look up the permission request by its ID in the database and confirm that:
        - It exists.
        - Its status is currently approved.
        - It belongs to the correct siteId and forMonth.
    - If any of these authorization checks fail, the request must be rejected with a 403 Forbidden or 400 Bad Request error.
2. **State Change (Crucial for Single-Use Permission):**
    - Upon successful creation of the indent, the backend **MUST** immediately and atomically change the status of the permission request (identified by extraMaterialRequestId) from approved to **closed**. This prevents the same approval from being used for multiple orders.
3. **Routing:** Create the indent with an initial status of PENDING_RM_APPROVAL.

### **4. Example JSON Payload**

**Example A: Regular Indent**
```json
{
    "siteId": "siteB",
    "forMonth": "October 2025",
    "isMonthly": true,
    "category": "Regular",
    "items": [
        {
            "productCode": "P03387",
            "quantity": 5
        },
        {
            "productCode": "P03386",
            "quantity": 2
        }
    ]
}
```

**Example B: Extra Material Indent**
```json
{
    "siteId": "siteC",
    "forMonth": "November 2025",
    "isMonthly": false,
    "category": "Extra Material",
    "items": [
        {
            "productCode": "P05112",
            "quantity": 50
        },
        {
            "productCode": "P05113",
            "quantity": 25
        }
    ],
    "extraMaterialRequestId": "EMR-2025-102"
}
```

**5. Success Response (201 Created)**

Upon successful creation of either type of indent, the API should respond with a confirmation, including the newly generated Tracking ID and the initial status.

```json
{
    "message": "Indent submitted successfully.",
    "trackingNo": "IND/2025/50815",
    "status": "PENDING_RM_APPROVAL"
}
```

# 8. API Specification: Indent Approval & PO Creation 

This details all APIs required for the "Create Purchase Order" page, which serves as the Procurement Head's final approval workspace.

**1. API to Fetch Indents for Approval (List View)**

Populates the main "Approval" tab with indents awaiting a decision.

- **Endpoint:** GET /api/indents
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - status (string, required): Fixed to PENDING_PH_APPROVAL.
    - search (string, optional): Filters results by Tracking No or Site Name.
    - page (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination and an array of ManagerIndent summaries.
```json
{
    "pagination": {
        "currentPage": 1,
        "totalPages": 5,
        "totalItems": 48
    },
    "indents": [
        {
            "trackingNo": "IND/2025/50808",
            "monthYear": "September 2025",
            "requestDate": "2025-09-08",
            "siteName": "siteB",
            "branchName": "DUMMY BRANCH",
            "category": "Regular",
            "requestCategory": "Chargeable",
            "siteBudget": 10000.00,
            "value": 1285.20,
            "balance": 8714.80,
            "status": "PENDING_PH_APPROVAL"
        }
    ]
}
```

**2. API to Fetch Full Indent Details (for View/Edit Modals)**

Called when the user clicks the "View" or "Edit" icon. It provides the complete data needed to populate the modals.

- **Endpoint:** GET /api/indents/{indentId}
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:**
    - {indentId} (string, required): The trackingNo of the indent.

**Success Response (200 OK)**

A single, detailed JSON object matching the IndentDetails structure.
```json
{
    "trackingNo": "IND/2025/50808",
    "requestDate": "2025-09-08",
    "monthYear": "September 2025",
    "branch": "DUMMY BRANCH",
    "branchGst": "27AAAAA0000A1Z5",
    "client": "ACME Corporation",
    "siteName": "siteB",
    "requestCategory": "Chargeable",
    "categoryType": "Regular",
    "narration": "Monthly restock of cleaning supplies.",
    "documentUrl": "https://storage.cloud.com/indent-docs/doc123.pdf",
    "vendor": "Multiple",
    "products": [
        {
            "srNo": 1,
            "productGroup": "MATERIAL",
            "productName": "ALL KLEAN - 1LTR",
            "productDescription": "Code: P03387",
            "unit": "NOS",
            "vendor": "SCHEVARAN - MS",
            "quantity": 3,
            "rate": 86.40,
            "tax": 18,
            "amount": 259.20
        }
    ],
    "totalQty": 15,
    "salesTotalBeforeTax": 1100.00,
    "salesTotalAfterTax": 1285.20,
    "purchaseTotalBeforeTax": 1100.00,
    "purchaseTotalAfterTax": 1285.20
}
```

**3. API to Update an Indent (Save Changes from Edit Modal)**

Called when the Procurement Head saves changes in the "Edit Indent" modal.

- **Endpoint:** PUT /api/indents/{indentId}
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:**
    - {indentId} (string, required): The trackingNo of the indent.

**Request Body (JSON)**

A JSON object containing only the fields that are editable.

|   |   |   |
|---|---|---|
|**Field**|**Type**|**Required**|
|branchGst|String|Yes|
|requestCategory|String|Yes|
|narration|String|No|
|products|Array of Objects|Yes|

**products Object Structure:**

- productCode: (String)
- quantity: (Number) The potentially updated quantity.

**Example Payload**
```json
{
    "branchGst": "29BBBBB1111B1Z6",
    "requestCategory": "Non-Chargeable",
    "narration": "Updated quantity for All Klean as per new site requirement.",
    "products": [
        {
            "productCode": "P03387",
            "quantity": 5
        },
        {
            "productCode": "P03389",
            "quantity": 1
        }
    ]
}
```

**4. API to Approve Indents & Create PO(s)**

The core approval action for single or bulk indents.

- **Endpoint:** POST /api/indents/approve
- **Authorization:** **Procurement Head** role required.

**Request Body Example (Bulk/single Approval)**
```json
{
    "indentIds": [
        "IND/2025/50808",
        "IND/2025/50812"
    ]
}
```

**5. API to Reject an Indent**

Handles the rejection of a single indent.

- **Endpoint:** POST /api/indents/{indentId}/reject
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:** {indentId} (string)

**Request Body Example**
```json
{
    "reason": "The requested quantities exceed the quarterly forecast for this site. Please revise and resubmit if necessary."
}
```

**6. API to Fetch Site Order History**

This API populates the "Site Order History" tab, providing a historical view of all indents for a specific site and month.

- **Endpoint:** GET /api/sites/{siteId}/history
- **Authorization:** **Procurement Head** role required.
- **URL and Query Parameter Example:** /api/sites/siteB/history?month=2025-09

**Success Response (200 OK)**

The response is a JSON array of SiteOrderHistory objects for the specified site and month.
```json
[
    {
        "siteId": "siteB",
        "trackingNo": "IND/2025/50808",
        "requestDate": "2025-09-08",
        "siteBudget": 10000.00,
        "value": 1285.20,
        "status": "Approved",
        "balance": 8714.80
    },
    {
        "siteId": "siteB",
        "trackingNo": "IND/2025/50755",
        "requestDate": "2025-09-02",
        "siteBudget": 10000.00,
        "value": 3450.00,
        "status": "Approved",
        "balance": 6550.00
    }
]
```
# 9. API Specification: Vendor Purchase Order Management

This details the APIs required for the Vendor's Purchase Order (PO) page. Vendors use this page to view assigned POs, update their fulfilment status, and download relevant documents.

**1. API to Fetch Assigned Purchase Orders**

Populates the main table with all POs assigned to the authenticated vendor.

- **Endpoint:** GET /api/purchase-orders
- **Authorization:** **Vendor** role required.
- **Query Parameters:**
    - search (string, optional): Filters results by PO Number, Site Name, etc.
    - page (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination info and an array of PurchaseOrder objects.
```json
{
    "pagination": {
        "currentPage": 1,
        "totalPages": 3,
        "totalItems": 25
    },
    "purchaseOrders": [
        {
            "materialRequestId": "IND/2025/50808",
            "siteName": "siteB",
            "region": "West",
            "poNumber": "PO-951432",
            "poDate": "2025-10-28",
            "deliveryType": "Courier",
            "tat": 7,
            "expectedDeliveryDate": "2025-11-04",
            "status": "In Transit",
            "courierName": "Blue Dart",
            "podNumber": "BD12345678",
            "dateOfDelivery": null,
            "podImageUrl": null,
            "signedPodUrl": null,
            "signedDcUrl": null,
            "tatStatus": null,
            "reason": null
        }
    ]
}
```

**2. API to Update a Purchase Order**

This is the core endpoint for the "Edit" modal. It handles updating logistical information and uploading proof-of-delivery documents using the standard multipart/form-data format.

- **Endpoint**: PUT /api/purchase-orders/{poNumber}
- **Authorization**: Vendor role required (backend must verify the PO belongs to the vendor).
- **Request** **Format**: multipart/form-data
- **Description**: The request is composed of multiple parts: a JSON string named data for all text-based fields, and separate binary parts for each file upload.

**Request Body Parts**

**A. data (JSON String):** This part contains all the non-file information

|   |   |   |
|---|---|---|
|**Field**|**Type**|**Description**|
|deliveryType|"Hand" or "Courier"|The method of delivery.|
|courierName|String|Name of the courier service.|
|podNumber|String|Proof of Delivery number.|
|status|"In Transit", "Delivered", “Not Delivered(default)” .|The current status of the shipment.|
|dateOfDelivery|Date (ISO String)|The actual date the delivery was completed.|
|reason|String|Justification if the delivery is late.|

**B. File Parts (Binary Data):** These parts contain the actual file data.

- podImage: (File) Photo of the proof of delivery.
- signedPod: (File) The scanned, signed Proof of Delivery document.
- signedDc: (File) The scanned, signed Delivery Challan.

**Critical Backend Validations**

The backend must enforce the following rules. If any validation fails, the API should return a 400 Bad Request error with a clear message.

1. **Date Logic:** dateOfDelivery cannot be a future date.
2. **"Delivered" Status Validation (Strict):** If the status is set to "Delivered", **all of the following fields become mandatory**:
    - dateOfDelivery: Must be provided and be a valid date.
    - podNumber: Must be provided and not be an empty string.
    - The podImage file part must be present.
    - The signedPod file part must be present.
    - The signedDc file part must be present.
3. **Courier Logic:** If deliveryType is "Courier", the courierName field is mandatory.
4. **TAT & Reason Logic:** The backend must calculate the tatStatus internally. If the calculation results in "Out of TAT", the reason field becomes mandatory.

**Example Request Structure**

A complete request is a single multipart/form-data submission. Below are two scenarios illustrating which parts would be sent.

**Scenario A: Updating Status to "In Transit"**

- Part 1: data (JSON String)
```json
{
    "deliveryType": "Courier",
    "courierName": "Blue Dart",
    "podNumber": "BD12345678",
    "status": "In Transit",
    "dateOfDelivery": null,
    "reason": null
}
```

- (No file parts are included in this update)

**Scenario B: Updating Status to "Delivered"**

- Part 1: data (JSON String)

```json
{
    "deliveryType": "Courier",
    "courierName": "Delhivery",
    "podNumber": "DLV987654",
    "status": "Delivered",
    "dateOfDelivery": "2025-11-03T00:00:00.000Z",
    "reason": null
}
```

- Part 2: podImage (File)
    - Content-Type: image/jpeg
    - Content: (binary data for the actual pod_photo.jpeg file)
- Part 3: signedPod (File)
    - Content-Type: application/pdf
    - Content: (binary data for the actual signed_pod_document.pdf file)
- Part 4: signedDc (File)
    - Content-Type: application/pdf
    - Content: (binary data for the actual signed_dc_document.pdf file)

**3. API to Download PO/DC Documents**

This is a GET request. There is **no JSON body**. The type of document required is specified in a URL query parameter.

- **Endpoint:** GET /api/purchase-orders/{poNumber}/download

**Request Examples (URLs)**

- **To download the PO as a PDF:**  
    GET /api/purchase-orders/PO-951432/download?type=po_pdf
- **To download the PO as an Excel file:**  
    GET /api/purchase-orders/PO-951432/download?type=po_excel
- **To download the Delivery Challan as a PDF:**  
    GET /api/purchase-orders/PO-951432/download?type=dc_pdf

**Success Response (200 OK)**

The response is **not JSON**. It is a direct file stream. The browser will treat it as a download.

- **For PDF:**
    - Content-Type: application/pdf
    - Content-Disposition: attachment; filename="PO-951432.pdf"
- **For Excel:**
    - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    - Content-Disposition: attachment; filename="PO-951432.xlsx"

**4. API to Export PO List to Excel**

This is also a GET request with **no JSON body**. It exports the list of POs that the vendor sees in their table, respecting any search filters they have applied.

- **Endpoint:** GET /api/purchase-orders/export

**Request Examples (URLs)**

- **To export all purchase orders:**  
    GET /api/purchase-orders/export
- **To export a filtered list of purchase orders (e.g., searching for "siteB"):**  
    GET /api/purchase-orders/export?search=siteB

**Success Response (200 OK)**

The response is **not JSON**. It is a direct file stream for an Excel document.

- **Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet**
- **Content-Disposition: attachment; filename="Vendor_Purchase_Orders_2025-10-28.xlsx"**

# 10. API Specification: PO Status Tracking 

This outlines the APIs required for the Procurement Head's read-only PO Status Tracking dashboard. This interface is used to monitor the fulfillment status of all purchase orders across the system.

**1. API to Fetch All Purchase Orders (List View)**

This is the primary API that populates the main table with all purchase orders, allowing the PH to monitor them.

- **Endpoint:** GET /api/purchase-orders
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - search (string, optional): Filters results by any relevant field (PO Number, Site Name, Status, etc.).
    - page (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination details and an array of purchase order objects. Each object in the array must match the ReadOnlyPurchaseOrder interface exactly.

{

"pagination": { "currentPage": 1, "totalPages": 15, "totalItems": 145 },

"purchaseOrders": [

{

"materialRequestId": "IND/2025/50808",

"siteName": "siteB",

"region": "West",

"dcNumber": "DC-10234",

"poNumber": "PO-951432",

"dcDate": "2025-10-29",

"poDate": "2025-10-28",

"deliveryType": "Courier",

"tat": 7,

"courierName": "Blue Dart",

"podNumber": "BD12345678",

"podImageUrl": "https://storage.cloud.com/docs/pod-image.jpg",

"signedPodUrl": "https://storage.cloud.com/docs/signed-pod.pdf",

"signedDcUrl": "https://storage.cloud.com/docs/signed-dc-by-vendor.pdf",

"signedDcISmartUrl": "https://storage.cloud.com/docs/signed-dc-by-site.pdf",

"expectedDeliveryDate": "2025-11-04",

"status": "GRN_SUBMITTED",

"dateOfDelivery": "2025-10-29",

"tatStatus": "Within TAT",

"reason": null

}

]

}

**2. API to Download PO/DC Documents**

A single, flexible endpoint to handle the generation and download of all documents related to a specific PO.

- **Endpoint:** GET /api/purchase-orders/{poNumber}/download
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:**
    - {poNumber} (string, required): The PO number for the document.
- **Query Parameter:**
    - type (string, required): Specifies the document type. Allowed values: po_pdf, po_excel, dc_pdf.

**Success Response (200 OK)**

The response is a direct **file stream**, not JSON. The browser will initiate a download.

- **For PDF:** Content-Type: application/pdf
- **For Excel:** Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

**3. API to Export PO List to Excel**

Handles the "Export to Excel" button, which generates and downloads a report of the currently filtered list of POs.

- **Endpoint:** GET /api/purchase-orders/export
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - search (string, optional): The same search query from the list view to ensure the export matches the displayed data.

**Success Response (200 OK)**

The response is a direct **file stream** for an Excel document.

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="Purchase_Orders_YYYY-MM-DD.xlsx"

# 11. API Specification: Requestor PO Tracking & GRN Submission

This outlines the APIs for the Requestor's "My Purchase Orders" page, including tracking, GRN submission, and exporting.

**1. API to Fetch Requestor's Purchase Orders**

This is the primary API that populates the main table with all POs created from the authenticated Requestor's indents.

- **Endpoint:** GET /api/purchase-orders
- **Authorization:** **Requestor** role required.
- **Query Parameters:**
    - search (string, optional): Filters results by PO Number, Site Name, etc.
    - page (number, optional): For pagination.

**Success Response (200 OK) - Complete JSON Example**

A JSON object with pagination info and an array of PurchaseOrder objects. Each PO object must include the _indentDetailsPayload with its items array, as this is required to build the GRN form.

{

"pagination": {

"currentPage": 1,

"totalPages": 2,

"totalItems": 18,

"pageSize": 10

},

"purchaseOrders": [

{

"materialRequestId": "IND/2025/50808",

"siteName": "siteB",

"region": "West",

"dcNumber": "DC-10234",

"poNumber": "PO-951432",

"dcDate": "2025-10-29",

"poDate": "2025-10-28",

"deliveryType": "Courier",

"tat": 7,

"courierName": "Blue Dart",

"podNumber": "BD12345678",

"podImageUrl": "https://storage.cloud.com/docs/pod-image.jpg",

"signedPodUrl": "https://storage.cloud.com/docs/signed-pod.pdf",

"signedDcUrl": "https://storage.cloud.com/docs/signed-dc-by-vendor.pdf",

"signedDciSmartUrl": "https://storage.cloud.com/docs/signed-dc-by-site.pdf",

"expectedDeliveryDate": "2025-11-04",

"status": "Delivered",

"dateOfDelivery": "2025-10-29",

"tatStatus": "Within TAT",

"reason": null,

"_indentDetailsPayload": {

"trackingId": "IND/2025/50808",

"items": [

{

"productCode": "P03387",

"productName": "ALL KLEAN - 1LTR",

"quantity": 3,

"siteName": "siteB",

"landedPrice": 86.40

},

{

"productCode": "P03389",

"productName": "ALL OUT MACHINE - MS",

"quantity": 1,

"siteName": "siteB",

"landedPrice": 102.00

}

],

"isMonthly": true,

"forMonth": "September 2025",

"totalValue": 1285.20

}

}

]

}

**2. API to Submit a Goods Reception Note (GRN)**

This is the core action endpoint for the GRN form. It associates the received items, feedback, and documents with the original PO and updates its status, only the POs with status as GRN_SUBMITTED will have GRN form enabled.

- **Endpoint:** POST /api/purchase-orders/{poNumber}/grn
- **Authorization:** **Requestor** role required (backend must verify the PO belongs to the user).
- **URL Parameter:**
    - {poNumber} (string, required): The PO Number for which the GRN is being created.
- **Request Format:** multipart/form-data. The request will contain a data field (JSON string) and parts for file uploads.

**Request Body Parts**

**A. data (JSON String):**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|items|Array of Objects|Yes|The list of verified items from the delivery.|
|predefinedComment|String|No|The selected option from the feedback dropdown.|
|comments|String|Conditional|Mandatory if predefinedComment is "OTHER".|

**items Object Structure:**  
_The frontend sends only what the user has entered, not the original order details._

|   |   |   |
|---|---|---|
|**Field**|**Type**|**Required**|
|itemId|String|Yes|
|receivedQuantity|Number|Yes|
|isAccepted|Boolean|Yes|

**B. File Parts (Binary Data):**

|   |   |
|---|---|
|**Field Name**|**Description**|
|photos|(Optional) Up to 2 image files for documenting delivery condition.|
|signedDc|(Required) A single PDF file of the signed Delivery Challan.|

**Critical Backend Logic**

1. **Data Reconciliation:** For each item submitted, the backend will retrieve the original orderedQuantity from its database and compare it to the receivedQuantity to determine if the delivery was partial, complete, or over-delivered. 
2. **File Requirements:** The signedDc file part is **mandatory**.
3. **Conditional Comment:** If predefinedComment is "OTHER", the comments field is mandatory.

**Example Request Structure**

A multipart/form-data request with these parts:

- **data field:**

{

"items": [

{ "itemId": "PO-951432-0", "receivedQuantity": 3, "isAccepted": true },

{ "itemId": "PO-951432-1", "receivedQuantity": 0, "isAccepted": false }

],

"predefinedComment": "SHORT_QUANTITY",

"comments": "The All Out Machine was missing from the delivery."

}

- **photos field:** (binary data for damaged_box.jpeg)
- **signedDc field:** (binary data for signed_delivery_challan.pdf)

**3. API to Download Documents**

A read-only endpoint for the Requestor to download the DC associated with a PO.

- **Endpoint:** GET /api/purchase-orders/{poNumber}/download
- **Authorization:** **Requestor** role required.
- **URL Parameter:**
    - {poNumber} (string, required): The PO number of the document.
- **Query Parameter:**
    - type (string, required): Specifies the document type. For the Requestor, this will primarily be dc_pdf.

**Example Request (URL)**

- GET /api/purchase-orders/PO-951432/download?type=dc_pdf

**Success Response (200 OK)**

The response is a direct **file stream**, not JSON. The browser will initiate a download.

- **Content-Type: application/pdf**
- **Content-Disposition: attachment; filename="DC-PO-951432.pdf"**

**4. API to Export PO List to Excel**

Handles the "Export to Excel" button, which generates and downloads a report of the currently filtered list of POs.

- **Endpoint:** GET /api/purchase-orders/export
- **Authorization:** **Requestor** role required.
- **Query Parameters:**
    - search (string, optional): The same search query from the list view to ensure the export matches the displayed data.

**Example Request (URL)**

- **To export a filtered list (e.g., searching for "siteB"):**  
    GET /api/purchase-orders/export?search=siteB

**Success Response (200 OK)**

The response is a direct **file stream** for an Excel document.

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="Requestor_Purchase_Orders_YYYY-MM-DD.xlsx"

# 12. API Specification: Vendor Invoice Upload

This details the APIs required for the Vendor's "Upload Invoices" page. This interface allows vendors to submit a single invoice against one or multiple Purchase Orders that have been confirmed as received via a Goods Reception Note (GRN).

**1. API to Fetch POs Ready for Invoicing**

This is the primary API that populates the main table with all POs eligible for invoicing for the authenticated vendor.

- **Endpoint:** GET /api/purchase-orders
- **Authorization:** **Vendor** role required.
- **Query Parameters:**
    - status (string, required): Fixed to GRN_SUBMITTED.
    - state (string, optional): Filters the POs by their state/region.
    - search (string, optional): Filters results by PO Number, Site Name, etc.
    - page (number, optional): For pagination.

**Success Response (200 OK) - Complete JSON Example**

A JSON object containing pagination details, a list of states for the filter dropdown, and a comprehensive array of PurchaseOrder objects. Each PO object includes all necessary nested data (grnDetails, _indentDetailsPayload) for the frontend to function correctly.

{

"pagination": {

"currentPage": 1,

"totalPages": 2,

"totalItems": 15,

"pageSize": 10

},

"availableStates": [

"West",

"South"

],

"purchaseOrders": [

{

"materialRequestId": "IND/2025/50808",

"siteName": "Mumbai Central Site",

"region": "West",

"dcNumber": "DC-10234",

"poNumber": "PO-951432",

"dcDate": "2025-10-29",

"poDate": "2025-10-28",

"deliveryType": "Courier",

"tat": 7,

"courierName": "Blue Dart",

"podNumber": "BD12345678",

"podImageUrl": "https://storage.cloud.com/docs/pod-image.jpg",

"signedPodUrl": "https://storage.cloud.com/docs/signed-pod.pdf",

"signedDcUrl": "https://storage.cloud.com/docs/signed-dc-by-vendor.pdf",

"expectedDeliveryDate": "2025-11-04",

"status": "GRN_SUBMITTED",

"dateOfDelivery": "2025-10-29",

"tatStatus": "Within TAT",

"reason": null,

"invoiceDetails": null,

"_indentDetailsPayload": {

"trackingId": "IND/2025/50808",

"items": [

{

"productCode": "P03387",

"productName": "ALL KLEAN - 1LTR",

"quantity": 3,

"siteName": "Mumbai Central Site",

"landedPrice": 86.40

},

{

"productCode": "P03389",

"productName": "ALL OUT MACHINE - MS",

"quantity": 1,

"siteName": "Mumbai Central Site",

"landedPrice": 102.00

}

],

"isMonthly": true,

"forMonth": "September 2025",

"totalValue": 361.20

},

"grnDetails": {

"items": [

{

"itemId": "PO-951432-0",

"itemName": "ALL KLEAN - 1LTR",

"orderedQuantity": 3,

"receivedQuantity": 3,

"isAccepted": true

},

{

"itemId": "PO-951432-1",

"itemName": "ALL OUT MACHINE - MS",

"orderedQuantity": 1,

"receivedQuantity": 1,

"isAccepted": true

}

],

"signedDc": "https://storage.cloud.com/grn-docs/signed-dc-by-site.pdf",

"comments": "All items received in good condition."

}

},

{

"materialRequestId": "IND/2025/50810",

"siteName": "Pune Westgate",

"region": "West",

"dcNumber": "DC-10235",

"poNumber": "PO-951435",

"dcDate": "2025-10-30",

"poDate": "2025-10-29",

"deliveryType": "Hand",

"tat": 3,

"courierName": null,

"podNumber": "Hand-Delivered",

"podImageUrl": "https://storage.cloud.com/docs/pod-image-2.jpg",

"signedPodUrl": "https://storage.cloud.com/docs/signed-pod-2.pdf",

"signedDcUrl": "https://storage.cloud.com/docs/signed-dc-by-vendor-2.pdf",

"expectedDeliveryDate": "2025-11-01",

"status": "GRN_SUBMITTED",

"dateOfDelivery": "2025-10-30",

"tatStatus": "Within TAT",

"reason": null,

"invoiceDetails": [

{

"id": "INV-XYZ789",

"invoiceNo": "INV-FINAL-789",

"state": "West",

"billAmount": 499.95,

"billUrl": "https://storage.cloud.com/invoices/inv-final-789.pdf",

"uploadedAt": "2025-10-31T10:00:00.000Z",

"status": "Pending",

"linkedPoNumbers": ["PO-951435"]

}

],

"_indentDetailsPayload": {

"trackingId": "IND/2025/50810",

"items": [

{

"productCode": "P04112",

"productName": "Safety Gloves (Pack of 10)",

"quantity": 5,

"siteName": "Pune Westgate",

"landedPrice": 99.99

}

],

"isMonthly": false,

"forMonth": "October 2025",

"totalValue": 499.95

},

"grnDetails": {

"items": [

{

"itemId": "PO-951435-0",

"itemName": "Safety Gloves (Pack of 10)",

"orderedQuantity": 5,

"receivedQuantity": 5,

"isAccepted": true

}

],

"signedDc": "https://storage.cloud.com/grn-docs/signed-dc-by-site-2.pdf",

"comments": ""

}

}

]

}

**2. API to Fetch Full Indent Details (for View PO Modal)**

This is the exact same API used on the PH's approval page. It's called when the vendor clicks the "View PO" icon to see the original material request details.

**3. API to Submit a New Invoice**

This is the core action endpoint for submitting the invoice form. It handles both single and multiple POs.

- **Endpoint:** POST /api/invoices
- **Authorization:** **Vendor** role required.
- **Request Format:** multipart/form-data with a data field (JSON string) and a file part for the bill.

**Request Body Parts**

**A. data (JSON String):**

|   |   |   |
|---|---|---|
|**Field**|**Type**|**Required**|
|poNumbers|Array of Strings|Yes|
|invoiceNo|String|Yes|
|state|String|Yes|
|billAmount|Number|Yes|

**B. File Part (Binary Data):**

|   |   |
|---|---|
|**Field Name**|**Description**|
|billUpload|(Required) A single PDF, JPG, or PNG file of the official invoice.|

**Critical Backend Validation Logic**

This is the most important step. Before accepting the invoice, the backend must perform this server-side check:

1. Fetch all POs listed in the poNumbers array.
2. For each PO, retrieve its GRN details.
3. Calculate the total expected billable amount based on the receivedQuantity from the GRN and the landedPrice of each product.
4. Compare this calculated server-side total with the billAmount submitted by the vendor.
5. If the amounts do not match exactly, the API must return a 400 Bad Request error with a clear message.
    - Error Message Example: "Invoice submission failed: The provided Bill Amount (₹15,250.50) does not match the calculated amount based on GRN records (₹15,200.00)."
6. If the amounts match, the API proceeds to save the invoice and link it to the POs.

**Example Request Structure**

- **data field:**

{

"poNumbers": ["PO-951432", "PO-951433"],

"invoiceNo": "INV-ABC-2025-101",

"state": "West",

"billAmount": 15200.00

}

- **billUpload field:** (binary data for official_invoice.pdf)

# 13. API Specification: Invoice Approval 

This details the APIs for the Procurement Head's "Invoice Approvals" page. This interface is the central command center for verifying and approving vendor invoices by matching them against Purchase Orders (POs) and Goods Reception Notes (GRNs).

**1. API to Fetch Invoices for Approval (List View)**

This is the primary API that populates the main table with all vendor invoices awaiting a decision.

- **Endpoint:** GET /api/invoices
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - status (string, optional): Filters by status (e.g., Pending, Approved).
    - search (string, optional): Filters by PO Number, Invoice No, etc.
    - site (string, optional): Filters by a specific Site Name.
    - state (string, optional): Filters by a specific State/Region.
    - page (number, optional): For pagination.

**Success Response (200 OK) - Complete JSON Example**

A JSON object with pagination, filter options, and an array of ApprovalInvoice objects.

{

"pagination": { "currentPage": 1, "totalPages": 4, "totalItems": 35 },

"filterOptions": {

"sites": ["siteB", "siteC"],

"states": ["West", "South"]

},

"invoices": [

{

"invoiceId": "INV-XYZ789",

"invoiceNo": "INV-ABC-2025-101",

"invoiceDate": "2025-10-31T10:00:00.000Z",

"billAmount": 1061.20,

"state": "West",

"billUrl": "https://storage.cloud.com/invoices/inv-abc-101.pdf",

"status": "Pending",

"relatedPurchaseOrders": [

{

"poNumber": "PO-951432",

"materialRequestId": "IND/2025/50808",

"siteName": "Mumbai Central Site",

"poDate": "2025-10-28"

},

{

"poNumber": "PO-951433",

"materialRequestId": "IND/2025/50809",

"siteName": "Pune Westgate",

"poDate": "2025-10-28"

}

],

"_poItems": [

{ "productName": "ALL KLEAN - 1LTR", "quantity": 3, "rate": 86.40, "amount": 259.20 },

{ "productName": "Safety Helmet", "quantity": 2, "rate": 401.00, "amount": 802.00 }

],

"_grnDetails": {

"items": [

{ "itemId": "PO-951432-0", "itemName": "ALL KLEAN - 1LTR", "orderedQuantity": 3, "receivedQuantity": 3, "isAccepted": true },

{ "itemId": "PO-951433-0", "itemName": "Safety Helmet", "orderedQuantity": 2, "receivedQuantity": 2, "isAccepted": true }

],

"signedDc": "https://storage.cloud.com/grn-docs/signed-dc-by-site.pdf",

"comments": "All items received in good condition.",

"packagingImages": [

"https://storage.cloud.com/grn-docs/package-img1.jpg"

]

}

},

{

"invoiceId": "INV-XYZ790",

"invoiceNo": "INV-DEF-2025-102",

"invoiceDate": "2025-11-01T11:00:00.000Z",

"billAmount": 350.00,

"state": "South",

"billUrl": "https://storage.cloud.com/invoices/inv-def-102.pdf",

"status": "Pending",

"relatedPurchaseOrders": [

{

"poNumber": "PO-951445",

"materialRequestId": "IND/2025/50815",

"siteName": "Chennai Site",

"poDate": "2025-10-27"

}

],

"_poItems": [

{ "productName": "Safety Helmet", "quantity": 2, "rate": 350.00, "amount": 700.00 }

],

"_grnDetails": {

"items": [

{ "itemId": "PO-951445-0", "itemName": "Safety Helmet", "orderedQuantity": 2, "receivedQuantity": 1, "isAccepted": true }

],

"signedDc": "https://storage.cloud.com/grn-docs/signed-dc-by-site-2.pdf",

"comments": "Partial delivery received. One helmet missing.",

"packagingImages": []

}

}

]

}

**2. API to Approve Invoices**

This endpoint remains the same as it operates on invoiceIds, which are unique.

- **Endpoint:** POST /api/invoices/approve
- **Authorization:** **Procurement Head** role required.
- **Request Body (JSON):**

{

"invoiceIds": ["INV-XYZ789", "INV-XYZ790"]

}

**3. API to Reject an Invoice**

This endpoint also remains the same, as it targets a single, unique invoiceId.

- **Endpoint:** POST /api/invoices/{invoiceId}/reject
- **Authorization:** **Procurement Head** role required.
- **Request Body (JSON):**

{

"reason": "Invoice amount (₹350.00) does not match GRN value (₹700.00) due to partial delivery. Please submit a revised invoice."

}

# 14. API Specification: Extra Material Request Flow

This details the APIs required to power the ExtraMaterialFlowPage for the Requestor. This page serves as the entry point for the entire extra material workflow.

**1. API to Check Extra Material Permission Status**

This is the primary API for this flow. It is called when a Requestor selects a site to determine which UI to display (the request form, a pending message, or the order sheet). The backend will automatically check for a permission request corresponding to the **current month**.

- **Endpoint:** GET /api/extra-material-requests/status
- **Authorization:** **Requestor** role required.
- **Query Parameter:**
    - siteId (string, required): The unique ID of the selected site.

**Success Response (200 OK)**

A JSON object indicating the current status of the permission for the selected site and the current month.

- **Scenario A: No request exists, or the existing one is rejected or closed.**
    - The frontend will display the request form (ExtraMaterialRequestPage).

{

"status": "none"

}

- **Scenario B: A request has been submitted and is awaiting RM approval.**
    - The frontend will display the "Pending Approval" message.

{

"status": "pending",

"requestId": "EMR-2025-101"

}

- **Scenario C: The RM has approved the request, and ordering is now allowed.**
    - The frontend will display the product catalog (ExtraMaterialOrderSheet).

{

"status": "approved",

"requestId": "EMR-2025-101"

}

**2. API to Create an Extra Material Permission Request**

This API is called when the Requestor fills out and submits the form on the ExtraMaterialRequestPage.

- **Endpoint:** POST /api/extra-material-requests
- **Authorization:** **Requestor** role required.

**Request Body (JSON)**

The monthYear should be sent as a standardized string (e.g., ISO format) that the backend can easily parse.

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|siteId|String|Yes|The ID of the site the request is for.|
|monthYear|Date (ISO String)|Yes|The month and year the request applies to (e.g., "2025-11-01T00:00:00.000Z").|
|reason|String|Yes|The justification for needing extra materials.|

**Example Payload**

{

"siteId": "siteC",

"monthYear": "2025-11-01T00:00:00.000Z",

"reason": "Urgent plumbing repairs are required after an unexpected pipeline burst in the main facility."

}

# 15. API Specification: Extra Material Permission Approval

This details all APIs required for the Regional Manager's (RM) "Extra Material Approvals" page. This includes fetching pending requests, actioning them (approve/reject), and fetching historical data to support the decision-making process.

**1. API to Fetch Pending Permission Requests**

This is the primary API that populates the table with all extra material permission requests awaiting the RM's decision.

- **Endpoint:** GET /api/extra-material-requests
- **Authorization:** **Regional Manager** role required.
- **Query Parameters:**
    - status (string, required): This should be fixed to pending.
    - page (number, optional): For pagination.

A JSON object with pagination information and an array of ExtraMaterialRequest objects.

{

"pagination": { "currentPage": 1, "totalPages": 1, "totalItems": 3 },

"requests": [

{

"requestId": "EMR-2025-102",

"siteName": "siteC",

"monthYear": "November 2025",

"reason": "Urgent plumbing repairs are required after an unexpected pipeline burst in the main facility.",

"requesterName": "Anjali Sharma",

"requestDate": "2025-10-31T10:00:00.000Z",

"status": "pending"

},

{

"requestId": "EMR-2025-103",

"siteName": "siteA",

"monthYear": "November 2025",

"reason": "Additional safety equipment needed for a short-term construction project.",

"requesterName": "Rohan Mehra",

"requestDate": "2025-10-31T11:30:00.000Z",

"status": "pending"

}

]

}

**2. API to Approve Permission Requests**

This endpoint handles both single and bulk approvals, changing the status of the requests to approved.

- **Endpoint:** POST /api/extra-material-requests/approve
- **Authorization:** **Regional Manager** role required.

{

"requestIds": ["EMR-2025-102", "EMR-2025-103"]

}

**3. API to Reject a Permission Request**

This endpoint handles the rejection of a single permission request and requires a reason.

- **Endpoint:** POST /api/extra-material-requests/{requestId}/reject
- **Authorization:** **Regional Manager** role required.
- **URL Parameter:**
    - {requestId} (string, required): The ID of the permission request to reject.

{

"reason": "This requirement should be covered by the standard site budget. Please raise a regular indent."

}

**4. API to Fetch Site Indent History**

Provides the historical spending data for a specific site and month.

- **Endpoint:** GET /api/sites/{siteId}/indent-history
- **Authorization:** **Regional Manager** role required.
- **URL Parameter:**
    - {siteId} (string, required): The unique ID or name of the site.
- **Query Parameter:**
    - month (string, required): The month to fetch history for (format: "YYYY-MM").

GET /api/sites/siteC/indent-history?month=2025-11

An array of Indent summary objects for the specified site and month.

[

{

"trackingNo": "IND/2025/50755",

"category": "Regular",

"value": 3450.00,

"status": "PO_CREATED",

"siteName": "siteC",

"monthYear": "November 2025",

"siteBudget": 20000.00

},

{

"trackingNo": "IND/2025/50761",

"category": "Extra Material",

"value": 8500.00,

"status": "REJECTED_BY_PH",

"siteName": "siteC",

"monthYear": "November 2025",

"siteBudget": 20000.00

}

]

# 16. API Specification: Extra Material Order Sheet Data

This details the API required to populate the ExtraMaterialOrderSheet for a Requestor. This interface is displayed only after a Regional Manager has approved the Requestor's permission request for extra materials.

**1. API to Fetch the Master Product Catalog**

This is the sole API for this component. It is called when the ExtraMaterialOrderSheet is rendered. It provides the list of approved products in the system, along with the necessary filter options.

- **Endpoint:** GET /api/products/catalog
- **Authorization:** **Requestor** role required.
- **Action:** Returns the product catalog and filter data. The backend should ensure this endpoint is only accessible if the user has a valid, approved permission request (this can be inferred from the session or a token).

**Success Response (200 OK)**

A JSON object containing the dynamic filter options (categories and brands) and the complete array of Product objects.

{

"filterOptions": {

"categories": [

{ "value": "Fragrance", "label": "Fragrance" },

{ "value": "Soap - Liquid", "label": "Soap - Liquid" },

{ "value": "Safety Gear", "label": "Safety Gear" }

],

"brands": [

{ "value": "LOCAL", "label": "LOCAL" },

{ "value": "HUL", "label": "HUL" },

{ "value": "SafetyFirst", "label": "SafetyFirst" }

]

},

"products": [

{

"periodFrom": "22-Oct-24",

"vendorName": "MOPSHOP DISTRIBUTION PRIVATE LIMITED",

"productCode": "P03386",

"productName": "AIR DIFISUER MACHINE LOCAL - MS",

"landedPrice": 1740,

"manufacturedBy": "LOCAL",

"brandName": "LOCAL",

"hsnCode": "3925",

"packaging": "NOS",

"usedFor": "General",

"category": "Fragrance",

"lifeCycleDays": 365,

"costOfTransportationPerKM": 3,

"orderLeadTimeDays": 10,

"deliveryBy": "Direct to site by Vendor - Delivery per km",

"netProductCostPerDay": 4.77,

"gstSetOffAvailable": true,

"financeTreatment": "Depriciate"

},

{

"periodFrom": "22-Oct-24",

"vendorName": "MOPSHOP DISTRIBUTION PRIVATE LIMITED",

"productCode": "P03387",

"productName": "ALA BLEACH / RIN ALA (500 ML)HUL - MS",

"landedPrice": 94.8,

"manufacturedBy": "HUL",

"brandName": "HUL",

"hsnCode": "3402",

"packaging": "NOS",

"usedFor": "",

"category": "Soap - Liquid",

"lifeCycleDays": 30,

"costOfTransportationPerKM": 3,

"orderLeadTimeDays": 10,

"deliveryBy": "Direct to site by Vendor - Delivery per km",

"netProductCostPerDay": 3.16,

"gstSetOffAvailable": true,

"financeTreatment": "Depriciate"

}

]

}

# 17. API Specification: Regional Manager Indent Approval

This details all APIs required for the **Regional Manager's Approval Page**. This interface is functionally identical to the Procurement Head's page but serves as the first level of approval for "Extra Material" indents.

**1. API to Fetch Indents for Approval (RM Queue)**

This is the primary API that populates the main "Approval" tab with indents awaiting the Regional Manager's decision.

- **Endpoint:** GET /api/indents
- **Authorization:** **Regional Manager** role required.
- **Query Parameters:**
    - status (string, required): This must be fixed to **PENDING_RM_APPROVAL**.
    - search (string, optional): Filters results by Tracking No or Site Name.
    - page (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination and an array of ManagerIndent summaries. The status field will reflect the RM's queue.

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 18 },

"indents": [

{

"trackingNo": "IND/2025/50815",

"monthYear": "November 2025",

"requestDate": "2025-11-01",

"siteName": "siteC",

"branchName": "DUMMY BRANCH",

"category": "Extra Material",

"requestCategory": "Chargeable",

"siteBudget": 20000.00,

"value": 8500.00,

"balance": 11500.00,

"status": "PENDING_RM_APPROVAL"

}

]

}

**2. API to Fetch Full Indent Details (for View/Edit Modals)**

_This API is identical to the one used by the Procurement Head._ It is called when the RM clicks the "View" or "Edit" icon.

- **Endpoint:** GET /api/indents/{indentId}
- **Authorization:** **Regional Manager** role required.
- **URL Parameter:** {indentId} (string)

**3. API to Update an Indent (Save Changes from Edit Modal)**

_This API is identical to the one used by the Procurement Head._ It is called when the RM saves changes in the "Edit Indent" modal before approval.

- **Endpoint:** PUT /api/indents/{indentId}
- **Authorization:** **Regional Manager** role required.
- **URL Parameter:** {indentId} (string)

**4. API to Approve an Indent (RM Step)**

This is the core approval action for the RM. Upon success, the indent is moved to the next stage in the workflow.

- **Endpoint:** POST /api/indents/approve
- **Authorization:** **Regional Manager** role required.
- **Backend Logic:** Upon receiving this request from an RM, the backend changes the status of the specified indents from PENDING_RM_APPROVAL to **PENDING_PH_APPROVAL**. It does **not** create a PO at this stage.

**Request Body (JSON)**

_(This supports single or bulk approval, just like the PH's page)_

{

"indentIds": [

"IND/2025/50815",

"IND/2025/50816"

]

}

**5. API to Reject an Indent (RM Step)**

Handles the rejection of a single indent by the RM.

- **Endpoint:** POST /api/indents/{indentId}/reject
- **Authorization:** **Regional Manager** role required.
- **URL Parameter:** {indentId} (string)
- **Backend Logic:** The backend changes the indent's status to **REJECTED_BY_RM**.

**Request Body (JSON)**

{

"reason": "This expenditure was not pre-approved in the quarterly planning. Please provide more justification."

}

**6. API to Fetch Site Order History**

_This API is identical to the one used by the Procurement Head._ It populates the "Site Order History" tab.

- **Endpoint:** GET /api/sites/{siteId}/history
- **Authorization:** **Regional Manager** role required.
- **URL Parameter:** {siteId} (string)
- **Query Parameter:** month (string, "YYYY-MM")

# 18. API Specification: Create Cash Purchase Request 

This details the API required for a **Requestor** to submit a "Cash Purchase Request". This workflow is for items that are not available in the standard catalog and must be purchased externally.

**1. Endpoint & Authorization**

- **Endpoint:** POST /api/cash-purchases
- **Authorization:** **Requestor** role required.
- **Request Format:** multipart/form-data. The request must contain a data field (as a JSON string) and a separate part for the billUpload file.

**2. Request Body Parts**

#### **A. data (JSON String)**

This part contains all the non-file information for the cash purchase.

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|siteId|String|Yes|The unique identifier for the site the purchase was made for.|
|forTheMonth|Date (ISO String)|Yes|The month and year the purchase applies to (e.g., "2025-11-01T00:00:00.000Z").|
|vendorName|String|No|The name of the vendor from whom the items were purchased.|
|gstNo|String|No|The GST number of the vendor, if available.|
|products|Array of Objects|Yes|A list of one or more products that were purchased.|

**products Object Structure:**

|   |   |   |
|---|---|---|
|**Field**|**Type**|**Required**|
|productName|String|Yes|
|quantity|Number|Yes|
|cost|Number|Yes|

#### **B. billUpload (File Part)**

|   |   |
|---|---|
|**Field Name**|**Description**|
|billUpload|(Required) A single PDF, JPG, or PNG file of the purchase bill/invoice.|

**3. Example Request Structure**

A complete request is a single multipart/form-data submission. Below are the parts it would contain.

- **Part 1: data (JSON String)**

{

"siteId": "Site B",

"forTheMonth": "2025-11-01T00:00:00.000Z",

"vendorName": "Local Hardware Store",

"gstNo": "27ABCDE1234F1Z5",

"products": [

{

"productName": "Emergency LED Bulbs",

"quantity": 10,

"cost": 150

},

{

"productName": "Extension Cord (5m)",

"quantity": 2,

"cost": 300

}

]

}

- **Part 2: billUpload (File)**
    - Content-Type: application/pdf
    - Content: (binary data for the actual bill.pdf file)

# 19. API Specification: Cash Purchase Approval

This details the APIs required for the **Procurement Head's** "Cash Purchase Approvals" page. This interface is used to review and action cash purchase requests submitted by Requestors.

**1. API to Fetch Cash Purchase Requests (List View)**

This is the primary API that populates the main table with all cash purchase requests awaiting a decision.

- **Endpoint:** GET /api/cash-purchases
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - status (string, optional): Filters by status (e.g., "Pending", "Approved").
    - search (string, optional): Filters by Purchase ID, Requester Name, or Site.
    - page (number, optional): For pagination.

**Success Response (200 OK) - Complete JSON Example**

A JSON object with pagination information and an array of CashPurchaseApprovalItem objects. The list view contains all necessary data, including the nested products array.

{

"pagination": { "currentPage": 1, "totalPages": 3, "totalItems": 28 },

"purchases": [

{

"purchaseId": "CP-2025-5487",

"requesterName": "Anjali Sharma",

"requestDate": "2025-11-01",

"forTheMonth": "November 2025",

"site": "Site B",

"vendorName": "Local Hardware Store",

"gstNo": "27ABCDE1234F1Z5",

"billUrl": "https://storage.cloud.com/cash-bills/bill-5487.pdf",

"products": [

{ "productName": "Emergency LED Bulbs", "stock": 10, "cost": 150 },

{ "productName": "Extension Cord (5m)", "stock": 2, "cost": 300 }

],

"totalValue": 2100.00,

"status": "Pending"

},

{

"purchaseId": "CP-2025-5488",

"requesterName": "Rohan Mehra",

"requestDate": "2025-11-02",

"forTheMonth": "November 2025",

"site": "Site A",

"vendorName": "Quick Office Solutions",

"gstNo": null,

"billUrl": "https://storage.cloud.com/cash-bills/bill-5488.jpg",

"products": [

{ "productName": "Whiteboard Markers (Pack of 4)", "stock": 5, "cost": 120 }

],

"totalValue": 600.00,

"status": "Pending"

}

]

}

**2. API to Approve Cash Purchases**

This endpoint handles both single and bulk approvals.

- **Endpoint:** POST /api/cash-purchases/approve
- **Authorization:** **Procurement Head** role required.

**Example Payload**

{

"purchaseIds": ["CP-2025-5487", "CP-2025-5488"]

}

**3. API to Reject a Cash Purchase**

This endpoint handles the rejection of a single cash purchase and requires a reason.

- **Endpoint:** POST /api/cash-purchases/{purchaseId}/reject
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:**
    - {purchaseId} (string, required): The ID of the purchase to reject.

**Example Payload**

{

"reason": "This purchase exceeds the petty cash limit for the site. Please follow the standard procurement process."

}

# 20. API Specification: Bulk Product Upload

This details the APIs required for a **Vendor** to upload multiple products at once using a pre-formatted Excel template.

**1. API to Download the Product Template**

This endpoint provides the vendor with a correctly formatted .xlsx template.

- **Endpoint:** GET /api/products/bulk-upload-template
- **Authorization:** **Vendor** role required.

**Template Structure**

The backend is responsible for generating an Excel file with the following characteristics:

- **Columns:** The column headers in the template **must exactly match the fields of the single "Add Product" form**. This ensures a consistent data model. The required columns are:
    - Product Name
    - Category
    - Sub Category
    - Price
    - HSN Code
    - GST Rate (%)
    - UOM
    - Number of Delivery Days
    - Cost of Delivery
    - Description
- **Data Validation:** To guide the user and prevent errors, the backend should embed data validation rules (dropdown lists) directly into the Excel sheet for the Category, Sub Category, and UOM columns.

**Success Response (200 OK)**

The response is a direct **file stream**, not JSON. The browser will initiate a download.

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="Product_Upload_Template.xlsx"

**2. API to Upload and Process the Product File**

This is the core endpoint where the vendor submits their filled-out template. The backend is responsible for all parsing and validation.

- **Endpoint:** POST /api/products/bulk-upload
- **Authorization:** **Vendor** role required.
- **Request Format:** multipart/form-data.

**Request Body Parts**

|   |   |
|---|---|
|**Field Name**|**Description**|
|productsFile|(Required) The single .xlsx file containing the product data.|

**Critical Backend Logic**

1. Receive the raw Excel file.
2. Parse the file and verify that all required column headers are present.
3. Iterate through each data row, validating every cell against the business rules (e.g., Price > 0, HSN is 4 digits, Category is a valid option, etc.).
4. If any row fails validation, aggregate the errors. Do not process any data.
5. **If there are errors,** respond with a 400 Bad Request and a structured list of all errors.
6. **If all rows are valid,** add the new products to the system with a "Pending Approval" status.

**Success Response (200 OK)**

{

"message": "File processed successfully. 52 products have been submitted for approval."

}

**Error Response (400 Bad Request)**

{

"message": "File validation failed. Found 2 errors. Please correct the file and re-upload.",

"errors": [

{

"rowIndex": 5,

"productName": "Faulty Widget",

"error": "Price must be a positive number."

},

{

"rowIndex": 8,

"productName": "Another Item",

"error": "HSN Code must be exactly 4 digits."

}

]

}

# 21. API Specification: Vendor Product Management

This details the APIs required for the **Vendor's** "Manage My Products" page. This interface allows vendors to view their product catalog, request price changes, and remove products.

**1. API to Fetch Vendor's Products**

This is the primary API that populates the main table with all products associated with the authenticated vendor.

- **Endpoint:** GET /api/vendor/products
- **Authorization:** **Vendor** role required.
- **Query Parameters:**
    - page (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination information and an array of Product objects.

{

"pagination": { "currentPage": 1, "totalPages": 5, "totalItems": 48 },

"products": [

{

"productCode": "P03386",

"productName": "AIR DIFISUER MACHINE LOCAL - MS",

"category": "Fragrance",

"landedPrice": 1740.00,

"orderLeadTimeDays": 10

},

{

"productCode": "P03387",

"productName": "ALA BLEACH / RIN ALA (500 ML)HUL - MS",

"category": "Soap - Liquid",

"landedPrice": 94.80,

"orderLeadTimeDays": 10

}

]

}

**2. API to Submit a Product Price Change Request**

This API is called when a vendor submits the "Edit Product Price" modal. It does **not** update the price directly. Instead, it creates a new _approval request_ that is sent to the Procurement Head.

- **Endpoint:** POST /api/products/price-change-requests
- **Authorization:** **Vendor** role required.

**Request Body (JSON)**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|productId|String|Yes|The productCode of the product being edited.|
|newPrice|Number|Yes|The proposed new price for the product.|
|wefDate|Date (ISO String)|Yes|The future "With Effect From" date for the price change.|

**Critical Backend Validations**

1. **Price Validation:** The newPrice must be a positive number greater than zero.
2. **Date Validation:** The wefDate must be a future date (i.e., after the current date).
3. **Ownership:** The backend must verify that the productId belongs to the authenticated vendor making the request.

**Example Payload**

{

"productId": "P03387",

"newPrice": 99.50,

"wefDate": "2025-12-01T00:00:00.000Z"

}

**3. API to Delete a Product**

This endpoint is called when a vendor confirms their choice in the "Delete Product" dialog. This should be a hard delete or a soft delete (marking the product as inactive).

- **Endpoint:** DELETE /api/products/{productId}
- **Authorization:** **Vendor** role required.
- **URL Parameter:**
    - {productId} (string, required): The productCode of the product to be deleted.

**Critical Backend Validations**

1. **Ownership:** The backend must verify that the productId belongs to the authenticated vendor.
2. **Active Orders:** The backend should ideally prevent the deletion of a product that is part of an active, unfulfilled Purchase Order. If this check is implemented, a 400 Bad Request should be returned with an explanatory message.

**Success Response (200 OK or 204 No Content)**

A successful deletion can return a confirmation message or simply a 204 No Content status.

{

"message": "Product P03387 has been successfully deleted."

}

# 22. API Specification: Product Price Change Approval

This details the APIs required for the **Procurement Head's** "Product Edit Approvals" page. This interface is used to review and action price change requests submitted by Vendors.

**1. API to Fetch Price Change Requests (List View)**

This is the primary API that populates the main table with all product price change requests awaiting a decision.

- **Endpoint:** GET /api/products/price-change-requests
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - status (string, optional): Filters by status (e.g., "Pending", "Approved").
    - search (string, optional): Filters by Product Name or Product ID.
    - page (number, optional): For pagination.

**Success Response (200 OK) - Complete JSON Example**

A JSON object with pagination information and an array of ProductEditApprovalItem objects.

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 15 },

"requests": [

{

"approvalId": "PROD-EDIT-1735912800000",

"productId": "P03387",

"productName": "ALA BLEACH / RIN ALA (500 ML)HUL - MS",

"requesterName": "Global Supplies Co.",

"requestDate": "2025-11-01",

"originalPrice": 94.80,

"newPrice": 99.50,

"wefDate": "2025-12-01",

"status": "Pending"

},

{

"approvalId": "PROD-EDIT-1735912900000",

"productId": "P03386",

"productName": "AIR DIFISUER MACHINE LOCAL - MS",

"requesterName": "Local Distributors",

"requestDate": "2025-11-02",

"originalPrice": 1740.00,

"newPrice": 1750.00,

"wefDate": "2025-12-15",

"status": "Pending"

}

]

}

**2. API to Approve Price Change Requests**

This endpoint handles both single and bulk approvals. Upon approval, the backend is responsible for scheduling the price update to occur on the specified wefDate.

- **Endpoint:** POST /api/products/price-change-requests/approve
- **Authorization:** **Procurement Head** role required.

**Example Payload**

{

"approvalIds": ["PROD-EDIT-1735912800000", "PROD-EDIT-1735912900000"]

}

**3. API to Reject a Price Change Request**

This endpoint handles the rejection of a single price change request and requires a reason.

- **Endpoint:** POST /api/products/price-change-requests/{approvalId}/reject
- **Authorization:** **Procurement Head** role required.
- **URL Parameter:**
    - {approvalId} (string, required): The ID of the approval request to reject.

**Example Payload**

{

"reason": "The proposed price increase of 10% is too high. Please provide more justification or submit a revised request."

}

# 23. API Specification: Product Margin Management 

This details the APIs required for the **Procurement Head** to manage product margins. This feature allows for the bulk update of product selling prices by applying either a percentage margin or a direct amount over the vendor's price.

**1. API to Fetch Products for Margin Management**

This API provides the data needed to populate the main table on the "Manage Product Margins" page.

- **Endpoint:** GET /api/products/margins
- **Authorization:** **Procurement Head** role required.
- **Query Parameters:**
    - page (number, optional): For pagination.

**Success Response (200 OK)**

A JSON object with pagination and an array of ProductMarginData objects. The margin-related fields (marginPercentage, directMarginAmount, finalPriceWithMargin) will reflect the currently saved values in the database (or be null if not set).

{

"pagination": { "currentPage": 1, "totalPages": 10, "totalItems": 95 },

"products": [

{

"id": "P03387",

"title": "ALA BLEACH / RIN ALA (500 ML)HUL - MS",

"category": "Soap - Liquid",

"price": 94.80,

"deliveryDate": "2025-11-15",

"marginPercentage": 10,

"directMarginAmount": null,

"finalPriceWithMargin": 104.28

},

{

"id": "P04112",

"title": "Safety Helmet",

"category": "Safety Gear",

"price": 350.00,

"deliveryDate": "2025-11-18",

"marginPercentage": null,

"directMarginAmount": null,

"finalPriceWithMargin": null

}

]

}

**2. API to Download the Margin Template**

This endpoint generates and provides an Excel template pre-populated with the current product data. The user downloads this file, fills in the margin columns, and re-uploads it.

- **Endpoint:** GET /api/products/margins/export-template
- **Authorization:** **Procurement Head** role required.

**Template Structure**

The backend will generate an .xlsx file containing a snapshot of the current product data. The key columns for user input are Margin (%) and Direct Margin (₹). All other columns should be treated as read-only context for the user.

**Success Response (200 OK)**

A direct **file stream** for the Excel document.

- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
- Content-Disposition: attachment; filename="Product_Margins_Template_YYYY-MM-DD.xlsx"

**3. API to Upload and Process the Margin File**

This is the core endpoint where the PH submits the filled-out template. The backend is solely responsible for all parsing and validation.

- **Endpoint:** POST /api/products/margins/bulk-upload
- **Authorization:** **Procurement Head** role required.
- **Request Format:** multipart/form-data.

**Request Body Parts**

|   |   |
|---|---|
|**Field Name**|**Description**|
|marginFile|(Required) The single .xlsx file containing the product and margin data.|

**Critical Backend Logic**

1. Receive the raw Excel file.
2. Parse the file and verify required headers (Product ID, Margin (%), Direct Margin (₹)).
3. Iterate through each data row.
4. For each row:
    - Find the product in the database using the Product ID.
    - Check the Margin (%) and Direct Margin (₹) columns.
    - **Validation:** If **both** columns have a value, add an error for that row.
    - **Validation:** If a margin is provided, ensure it's a valid number.
    - If a row has no margin values, it is skipped.
5. If any row fails validation, aggregate all errors and do not apply any changes.
6. **If there are errors,** respond with a 400 Bad Request and a structured list of all errors.
7. **If all rows are valid,** calculate the new final prices for the valid rows and update the product pricing in the database.

**Success Response (200 OK)**

A successful response should confirm the update and return the newly calculated data for the frontend to refresh the table.

{

"message": "Margins for 25 products have been successfully updated.",

"updatedProducts": [

{

"id": "P03387",

"title": "ALA BLEACH / RIN ALA (500 ML)HUL - MS",

"category": "Soap - Liquid",

"price": 94.80,

"deliveryDate": "2025-11-15",

"marginPercentage": 10,

"directMarginAmount": null,

"finalPriceWithMargin": 104.28

},

{

"id": "P03386",

"title": "AIR DIFISUER MACHINE LOCAL - MS",

"category": "Fragrance",

"price": 1740.00,

"deliveryDate": "2025-11-20",

"marginPercentage": null,

"directMarginAmount": 160,

"finalPriceWithMargin": 1900.00

}

]

}

# 24. API Specification: Requestor's "My Indents" Page

This details the API required to populate the "Indents Created" page for the **Requestor**. This interface serves as a historical dashboard, allowing Requestors to view and track the status of all the material indents they have submitted.

**1. API to Fetch Requestor's Indents**

This is the primary API for this page. It is called to fetch all indents created by the authenticated user, which can then be filtered by the frontend.

- **Endpoint:** GET /api/indents/my-indents
- **Authorization:** **Requestor** role required (the backend will automatically filter for the logged-in user).

**Success Response (200 OK) - Complete JSON Example**

A JSON object containing a list of filterOptions for the dropdowns and a comprehensive indents array. Each indent object in the array represents a single, complete indent submission and contains all the nested product details.

{

"filterOptions": {

"sites": ["Site A", "Site B", "Site C"]

},

"indents": [

{

"trackingNo": "IND/2025/50808",

"monthYear": "October 2025",

"requestDate": "2025-10-26",

"siteName": "Site B",

"category": "Regular",

"isMonthly": true,

"siteBudget": 10000.00,

"totalValue": 361.20,

"status": "PENDING_PH_APPROVAL",

"items": [

{

"productCode": "P03387",

"productName": "ALL KLEAN - 1LTR",

"quantity": 3,

"landedPrice": 86.40,

"size": null

},

{

"productCode": "P03389",

"productName": "ALL OUT MACHINE - MS",

"quantity": 1,

"landedPrice": 102.00,

"size": null

}

]

},

{

"trackingNo": "IND/2025/50801",

"monthYear": "October 2025",

"requestDate": "2025-10-24",

"siteName": "Site A",

"category": "Regular",

"isMonthly": false,

"siteBudget": 15000.00,

"totalValue": 7999.90,

"status": "PO_CREATED",

"items": [

{

"productCode": "P04112",

"productName": "Safety Shoes",

"quantity": 10,

"landedPrice": 799.99,

"size": "9"

}

]

}

]

}

**Object Structures**

- **Main Indent Object:**
    - trackingNo (string)
    - monthYear (string)
    - requestDate (string, ISO format)
    - siteName (string)
    - category (string: "Regular" or "Extra Material")
    - isMonthly (boolean)
    - siteBudget (number)
    - totalValue (number)
    - status (string, e.g., "PENDING_PH_APPROVAL")
    - items (Array of Item Objects)
- **Item Object:**
    - productCode (string)
    - productName (string)
    - quantity (number)
    - landedPrice (number)
    - size (string or null)

# 25. API Specification: Notifications

This details the APIs required to power the NotificationsPage. The system is designed around the application's structure, where notifications link to specific management or approval pages rather than individual item detail pages.

**Backend Event-Driven Logic**

The backend should implement an event-driven system. When a key action occurs (e.g., a vendor submits a new product, an indent is approved), the system should generate a notification record in the database for the relevant user(s). The notification record must include a direct link to the appropriate page where the user can take action.

**1. API to Fetch User's Notifications**

This is the primary API that populates the NotificationsPage and provides the unread count for the sidebar badge.

- **Endpoint:** GET /api/notifications
- **Authorization:** Any authenticated user role.
- **Query Parameters:**
    - limit (number, optional): For pagination (e.g., 20).
    - page (number, optional): For pagination.

**Success Response (200 OK) - Complete JSON Example**

A JSON object with pagination, a total unreadCount, and an array of Notification objects. The link field contains a static path to the relevant page from the application's router.

{

"pagination": { "currentPage": 1, "totalPages": 5, "totalItems": 45 },

"unreadCount": 3,

"notifications": [

{

"id": "notif_p1",

"title": "Vendor Approval Required",

"message": "New vendor 'SteelTech Industries' is awaiting your approval.",

"date": "2025-10-31T11:20:00.000Z",

"isRead": false,

"link": "/vendor-approval"

},

{

"id": "notif_p4",

"title": "Price Change Request",

"message": "Vendor 'PipeMasters' has requested a price change for product #P-3456.",

"date": "2025-10-30T14:15:00.000Z",

"isRead": false,

"link": "/product-edit-approval"

},

{

"id": "notif_v3",

"title": "New PO Received",

"message": "You have received a new Purchase Order #PO-951432 from Site B.",

"date": "2025-10-28T09:15:00.000Z",

"isRead": false,

"link": "/vendor-purchase-orders"

},

{

"id": "notif_r2",

"title": "Indent Approved",

"message": "Your indent #IND/2025/50808 for Site B has been approved and a PO has been created.",

"date": "2025-10-28T09:14:00.000Z",

"isRead": true,

"link": "/indents"

}

]

}

**2. API to Mark Notifications as Read**

This API is used to update the isRead status of one or more notifications. It should be called when a user clicks on a notification or a "Mark all as read" button.

- **Endpoint:** POST /api/notifications/mark-as-read
- **Authorization:** Any authenticated user role.

**Request Body (JSON)**

The body accepts an array of notification IDs. Sending an empty array signifies "mark all unread notifications as read".

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|notificationIds|Array of Strings|Yes|An array of one or more ids of notifications to be marked as read.|

**Example Payload (Marking specific notifications)**

{

"notificationIds": ["notif_p1", "notif_p4"]

}

**Example Payload (Marking all as read)**

{

"notificationIds": []

}

**Comprehensive Notification Events**

This guide outlines the key business events within the procurement module that must trigger user notifications. The link provided in the API response should always direct the user to the relevant management page.

**1. Vendor Onboarding & Management**

|   |   |   |   |
|---|---|---|---|
|**Event**|**Triggered When...**|**Notifies**|**Notification Details**|
|**New Vendor Application**|A new vendor completes the 4-step registration form.|**Procurement Head**|**Title:** Vendor Approval Required <br> **Message:** New vendor "[Vendor Name]" has submitted their registration and is awaiting your approval. <br> **Link:** /vendor-approval|
|**Vendor Application Approved**|PH approves a vendor application.|**Vendor**|**Title:** Application Approved <br> **Message:** Congratulations! Your vendor application for "[Vendor Name]" has been approved. <br> **Link:** /vendor-dashboard|
|**Vendor Application Rejected**|PH rejects a vendor application.|**Vendor**|**Title:** Application Rejected <br> **Message:** Your vendor application was rejected. Reason: "[Rejection Reason]" <br> **Link:** /vendor-registration|

**2. Product Catalog Management**

|   |   |   |   |
|---|---|---|---|
|**Event**|**Triggered When...**|**Notifies**|**Notification Details**|
|**New Product Submitted**|A vendor submits a new product (single or bulk).|**Procurement Head**|**Title:** New Product for Approval <br> **Message:** Vendor "[Vendor Name]" has submitted a new product "[Product Name]" for approval. <br> **Link:** /product-approval|
|**Product Approved**|PH approves a new product.|**Vendor**|**Title:** Product Approved <br> **Message:** Your product "[Product Name]" has been approved and is now live in the catalog. <br> **Link:** /vendor-manage-products|
|**Product Rejected**|PH rejects a new product.|**Vendor**|**Title:** Product Rejected <br> **Message:** Your product "[Product Name]" was rejected. Reason: "[Rejection Reason]" <br> **Link:** /product-upload|
|**Price Change Requested**|A vendor submits a price change request.|**Procurement Head**|**Title:** Price Change Request <br> **Message:** Vendor "[Vendor Name]" has requested a price change for "[Product Name]". <br> **Link:** /product-edit-approval|
|**Price Change Approved**|PH approves a price change.|**Vendor**|**Title:** Price Change Approved <br> **Message:** Your price change request for "[Product Name]" has been approved. <br> **Link:** /vendor-manage-products|
|**Price Change Rejected**|PH rejects a price change.|**Vendor**|**Title:** Price Change Rejected <br> **Message:** Your price change request for "[Product Name]" was rejected. Reason: "[Rejection Reason]" <br> **Link:** /vendor-manage-products|

**3. Indent & Purchase Order (PO) Lifecycle**

|   |   |   |   |
|---|---|---|---|
|**Event**|**Triggered When...**|**Notifies**|**Notification Details**|
|**Regular Indent Submitted**|A Requestor submits a "Regular" indent.|**Procurement Head**|**Title:** New Indent for Approval <br> **Message:** New indent #[Tracking No] from "[Site Name]" is awaiting your approval. <br> **Link:** /create-purchase-order|
|**Extra Material Request Submitted**|A Requestor submits a request for extra material permission.|**Regional Manager**|**Title:** Extra Material Request <br> **Message:** A new extra material permission request from "[Site Name]" is awaiting your approval. <br> **Link:** /extra-material-approval|
|**Extra Material Request Approved**|RM approves the permission request.|**Requestor**|**Title:** Request Approved <br> **Message:** Your request for extra material at "[Site Name]" has been approved. You can now place the order. <br> **Link:** /extra-material-flow|
|**Extra Material Request Rejected**|RM rejects the permission request.|**Requestor**|**Title:** Request Rejected <br> **Message:** Your request for extra material at "[Site Name]" was rejected. Reason: "[Rejection Reason]" <br> **Link:** /extra-material-flow|
|**Extra Material Indent Submitted**|A Requestor submits an "Extra Material" indent.|**Regional Manager**|**Title:** Indent for Approval <br> **Message:** Extra material indent #[Tracking No] from "[Site Name]" is awaiting your final financial approval. <br> **Link:** /rm-indents-approval|
|**Extra Material Indent Approved by RM**|RM approves an "Extra Material" indent.|**Procurement Head**|**Title:** RM Approved Indent <br> **Message:** Indent #[Tracking No] has been approved by the RM and is awaiting your final review. <br> **Link:** /create-purchase-order|
|**Indent Approved & PO Created**|PH approves any indent, generating a PO.|**Vendor** & **Requestor**|**Vendor:** You have received a new Purchase Order #[PO Number] from "[Site Name]". <br> **Requestor:** Your indent #[Tracking No] has been approved and PO #[PO Number] has been created. <br> **Links:** /vendor-purchase-orders (Vendor), /requestor-po (Requestor)|
|**Indent Rejected**|RM or PH rejects any indent.|**Requestor**|**Title:** Indent Rejected <br> **Message:** Your indent #[Tracking No] has been rejected. Reason: "[Rejection Reason]" <br> **Link:** /indents|

**4. Delivery & Invoicing**

|   |   |   |   |
|---|---|---|---|
|**Event**|**Triggered When...**|**Notifies**|**Notification Details**|
|**PO Status Updated by Vendor**|Vendor updates a PO status (e.g., to "In Transit" or "Delivered").|**Requestor**|**Title:** Order Status Update <br> **Message:** Your order #[PO Number] has been updated to "[New Status]". <br> **Link:** /requestor-po|
|**GRN Submitted by Requestor**|A Requestor submits a GRN for a delivered PO.|**Vendor**|**Title:** GRN Submitted <br> **Message:** GRN has been submitted for your delivery against PO #[PO Number]. You can now upload your invoice. <br> **Link:** /vendor-invoice-upload|
|**Invoice Submitted by Vendor**|A vendor uploads an invoice.|**Procurement Head**|**Title:** New Invoice for Approval <br> **Message:** Invoice #[Invoice No] from "[Vendor Name]" is awaiting your approval. <br> **Link:** /invoice-approval|
|**Invoice Approved**|PH approves an invoice for payment.|**Vendor**|**Title:** Invoice Approved <br> **Message:** Your invoice #[Invoice No] has been approved and is scheduled for payment. <br> **Link:** /vendor-invoice-upload|
|**Invoice Rejected**|PH rejects an invoice.|**Vendor**|**Title:** Invoice Rejected <br> **Message:** Your invoice #[Invoice No] was rejected. Reason: "[Rejection Reason]" <br> **Link:** /vendor-invoice-upload|
|**Cash Purchase Submitted**|A Requestor submits a cash purchase form.|**Procurement Head**|**Title:** Cash Purchase Approval <br> **Message:** A new cash purchase request #[Purchase ID] from "[Site Name]" is awaiting your approval. <br> **Link:** /cash-purchase-approval|
|**Cash Purchase Approved/Rejected**|PH approves or rejects a cash purchase.|**Requestor**|**Title:** Cash Purchase [Status] <br> **Message:** Your cash purchase request #[Purchase ID] has been [Approved/Rejected]. <br> **Link:** /cash-purchase-requirements|

# 26. API Specification: Fetch Site Options

This API populates the "Select Site" dropdown, providing a list of sites the user is authorized to request for.

- **Endpoint:** GET /api/sites/options
- **Authorization:** Site Manager role required.
- **Success Response (200 OK):**  
    A JSON array of site objects.

[

{ "value": "SITE-001", "label": "Site A - Mumbai HQ" },

{ "value": "SITE-002", "label": "Site B - Bangalore Campus" },

{ "value": "SITE-003", "label": "Site C - Delhi Branch" }

]

# 27. API Specification: Fetch Machine Options

This API populates the "Machine Name" dropdown within the request table, providing a list of available machinery.

- **Endpoint:** GET /api/machinery/options
- **Authorization:** Site Manager role required.
- **Success Response (200 OK):**  
    A JSON array of machine objects.

[

{ "value": "Single Disc Scrubber", "label": "Single Disc Scrubber" },

{ "value": "High Pressure Jet", "label": "High Pressure Jet" },

{ "value": "Vacuum Cleaner (Wet/Dry)", "label": "Vacuum Cleaner (Wet/Dry)" }

]

# 28. API Specification: Submit Machinery Requisition

This API is called when the Site Manager submits the machinery request form. It captures all details for the procurement head's review.

- **Endpoint:** POST /api/machinery-requests
- **Authorization:** Site Manager role required.
- **Request Body:**  
    A JSON object with the following structure:

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|siteId|String|Yes|The unique ID of the selected site (e.g., "SITE-001").|
|justification|String|Yes|Detailed reason for the request. Min 5 characters.|
|items|Array of Objects|Yes|List of machines being requested. Must contain at least one item.|

**Structure of items Array Object:**  

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|machineName|String|Yes|Name of the machine.|
|quantity|Number|Yes|Must be a positive integer (minimum value: 1).|
|requestType|String|Yes|Type of request.|
|oldAssetId|String|Conditional|Required if requestType is **"replacement"**.|

**Example JSON Payload:**

{

"siteId": "SITE-002",

"justification": "New wing opened in the Bangalore campus, requiring an additional scrubber for the larger floor area.",

"items": [

{

"machineName": "Auto Scrubber",

"quantity": 1,

"requestType": "new"

},

{

"machineName": "Vacuum Cleaner (Wet/Dry)",

"quantity": 1,

"requestType": "replacement",

"oldAssetId": "ASSET-VC-045"

}

]

}

- **Validation & Business Logic:**
    - requestType: Must be one of ["new", "replacement"].
    - **Conditional Validation:** The backend must validate that oldAssetId is present and not an empty string if requestType is "replacement".
    - **Backend Actions:**
        - Generate a unique Requisition ID (e.g., MREQ-12345).
        - Set the initial status to PENDING_PH_APPROVAL.

# 29. API Specification: Fetch Machinery Requests (Approval View)

This API populates the main "Machinery Approvals" table with requests that are pending review.

- **Endpoint:** GET /api/machinery-requests
- **Authorization:** Procurement Head role required.
- **Query Parameters:**
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.
- **Success Response (200 OK):**  
    A JSON object containing the list of pending requests.

{

"pagination": { "currentPage": 1, "totalPages": 3, "totalItems": 28 },

"requests": [

{

"id": "MREQ-12345",

"siteName": "Site B - Bangalore Campus",

"requestDate": "2023-11-10T10:00:00Z",

"status": "PENDING_PH_APPROVAL",

"items": [

{

"machineName": "Auto Scrubber",

"quantity": 1,

"requestType": "new"

},

{

"machineName": "Vacuum Cleaner (Wet/Dry)",

"quantity": 1,

"requestType": "replacement",

"oldAssetId": "ASSET-VC-045"

}

]

}

]

}

# 30. API Specification: Fetch Full Request Details for Approval

This API is called when the Procurement Head clicks "Review". It fetches the complete request details _and_ cross-references the required machines against the global asset inventory to find available spares for transfer.

- **Endpoint:** GET /api/machinery-requests/{requestId}/details-for-approval
- **Authorization:** Procurement Head role required.
- **Success Response (200 OK):**  
    A single JSON object containing the full request and available inventory.

{

"id": "MREQ-12345",

"siteName": "Site B - Bangalore Campus",

"justification": "New wing opened, and old vacuum cleaner is non-functional.",

"requestDate": "2023-11-10T10:00:00Z",

"items": [

{

"machineName": "Auto Scrubber",

"quantity": 1,

"requestType": "new",

"availableInventory": []

},

{

"machineName": "Single Disc Scrubber",

"quantity": 1,

"requestType": "replacement",

"oldAssetId": "ASSET-SDS-012",

"availableInventory": [

{ "site": "Site A - Mumbai", "serial": "MAC-004", "status": "Idle" },

{ "site": "Warehouse", "serial": "MAC-009", "status": "Spare" }

]

}

]

}

# 31. API Specification: Fetch Machinery Vendors

This API populates the vendor dropdown in the modal when "Purchase New" is selected as the decision.

- **Endpoint:** GET /api/vendors/category/machinery
- **Authorization:** Procurement Head role required.
- **Success Response (200 OK):**

[

{ "value": "VEN-M01", "label": "Heavy Duty Equipments Ltd" },

{ "value": "VEN-M02", "label": "CleanTech Solutions" }

]

# 32. API Specification: Fulfill Machinery Request

This API is called when the PH clicks "Confirm Allocation". It is a critical transaction that creates Purchase Orders for new buys and Transfer Orders for internal movements based on the decisions made.

- **Endpoint:** POST /api/machinery-requests/{requestId}/fulfill
- **Authorization:** Procurement Head role required.
- **Request Body:**  
    A JSON object containing an array of decisions for each item in the request.

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|decisions|Array of Objects|Yes|An array mapping each requested item to a fulfillment action.|

**Structure of decisions Object:**

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|machineName|String|Yes|Name of the machine this decision applies to.|
|quantity|Number|Yes|The quantity this decision covers.|
|source|String|Yes|The fulfillment method. Must be **"PURCHASE"** or **"TRANSFER"**.|
|vendorId|String|Conditional|Required if source is **"PURCHASE"**.|
|sourceSiteId|String|Conditional|Required if source is **"TRANSFER"**|

**Example JSON Payload:**

{

"decisions": [

{

"machineName": "Auto Scrubber",

"quantity": 1,

"source": "PURCHASE",

"vendorId": "VEN-M02"

},

{

"machineName": "Single Disc Scrubber",

"quantity": 1,

"source": "TRANSFER",

"sourceSiteId": "009"

}

]

}

- **Backend Business Logic:**
    1. **Process Purchases:** For all items with source: "PURCHASE", group them by vendorId and create a distinct **Machinery Purchase Order** for each vendor. The backend must look up the price for each machine from a master price list.
    2. **Process Transfers:** For all items with source: "TRANSFER", create a Machinery Transfer Order
    3. **Update Request:** Set the status of the original MachineryRequest to PROCESSED.

# 33. API Specification: Reject Machinery Request

This API handles the rejection of a machinery request.

- **Endpoint:** POST /api/machinery-requests/{requestId}/reject
- **Authorization:** Procurement Head role required.
- **Request Body:**

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|reason|String|Yes|A detailed reason for the rejection.|

  

**Example JSON Payload:**

{

"reason": "The existing machine at the site can be repaired. A new purchase is not justified at this time."

}

# 34. API Specification: Vendor Machinery Purchase Orders

This section details the APIs required for vendors to list, view, update, and generate documents for their assigned Machinery Purchase Orders.

**1. API to Fetch Machinery Purchase Orders**

This API populates the main table with Machinery POs assigned to the authenticated vendor.

- **Endpoint:** GET /api/vendor/machinery-orders
- **Authorization:** Vendor role required.
- **Query Parameters:**
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.
    - search (string, optional): Matches against Site Name or PO Number.
- **Success Response (200 OK):**  
    A JSON object containing the list of POs.

{

"pagination": { "currentPage": 1, "totalPages": 4, "totalItems": 35 },

"orders": [

{

"id": "uuid-mac-123",

"poNumber": "PO-MAC-98765",

"poDate": "2023-11-10T12:00:00Z",

"vendorName": "Heavy Duty Equipments Ltd",

"vendorId": "VEN-M01",

"siteName": "Site B - Bangalore Campus",

"region": "Karnataka",

"status": "In Transit",

"deliveryType": "Courier",

"courierName": "Delhivery",

"podNumber": "DEL987654321",

"expectedDeliveryDate": "2023-11-17",

"dateOfDelivery": null,

"tat": 7,

"tatStatus": "Within TAT",

"reason": null,

"podImageUrl": null,

"signedPodUrl": null,

"signedDcUrl": null,

"items": [

{

"productName": "Auto Scrubber",

"quantity": 1,

"landedPrice": 150000

}

]

}

]

}

**2. API to Fetch Single Machinery PO Details**

Used when the vendor clicks the "View" or "Edit" (Pencil icon) to populate the modal with detailed information.

- **Endpoint:** GET /api/purchase-orders/machinery/{poNumber}
- **Authorization:** Vendor role required.
- **Success Response (200 OK):** Returns the full MachineryPurchaseOrder object

**3. API to Update Machinery Purchase Order**

This API is called when the vendor submits the "Edit" form to update delivery status and upload proof of delivery documents.

- **Endpoint:** PUT /api/purchase-orders/machinery/{poNumber}
- **Authorization:** Vendor role required.
- **Request Body & Behavior:**
    - **Note:** The Request Body structure, validation rules, and business logic for this endpoint are identical to the **Material Purchase Order Update API**.
    - This API handles multipart/form-data requests to update fields such as status, deliveryType, courierName, podNumber, dateOfDelivery, reason, and upload files for podImage, signedPod, and signedDc. Please refer to that specification for the exact field definitions.

**4. API for Document Generation and Export**

These endpoints generate and serve files based on user actions in the table.

**A. Generate PO PDF**

- **Trigger:** Click on the "Print" icon.
- **Endpoint:** GET /api/purchase-orders/machinery/{poNumber}/pdf
- **Response:** A binary file (application/pdf) of the formatted Purchase Order.

**B. Generate Delivery Challan (DC)**

- **Trigger:** Click on the "DC" icon.
- **Endpoint:** GET /api/purchase-orders/machinery/{poNumber}/dc-pdf
- **Response:** A binary file (application/pdf) of the Delivery Challan.

**C. Export to Excel**

- **Trigger (Single):** Click on the "Excel" icon in a row.
    - **Endpoint:** GET /api/purchase-orders/machinery/{poNumber}/export
- **Trigger (All):** Click the "Export All to Excel" button.
    - **Endpoint:** GET /api/vendor/machinery-orders/export-all
- **Response:** A binary file with the content type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.

# 35. API Specification: Requestor Machinery PO & GRN

This section details the APIs for the Requestor to manage their site's machinery orders and acknowledge their receipt by submitting a Goods Reception Note (GRN).

**1. API to Fetch My Machinery Orders**

This API populates the requestor's dashboard with Machinery POs relevant to their site.

- **Endpoint:** GET /api/requestor/machinery-orders
- **Authorization:** Requestor role.
- **Query Parameters:**
    - page (number, optional)
    - limit (number, optional)
    - search (string, optional): Matches against PO Number, Site Name, or Vendor.
- **Success Response (200 OK):**  
    A JSON object with pagination and an array of order objects.

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 15 },

"orders": [

{

"id": "uuid-mac-123",

"poNumber": "PO-MAC-98765",

"poDate": "2023-11-10T12:00:00Z",

"vendorName": "Heavy Duty Equipments Ltd",

"siteName": "Site B - Bangalore Campus",

"region": "Karnataka",

"status": "Delivered",

"deliveryType": "Courier",

"courierName": "Delhivery",

"podNumber": "DEL987654321",

"dcNumber": "DC-VENDOR-556",

"dcDate": "2023-11-15",

"expectedDeliveryDate": "2023-11-17",

"dateOfDelivery": "2023-11-16",

"tat": 7,

"tatStatus": "Within TAT",

"reason": null,

"podImageUrl": "https://storage.cloud.com/pods/pod-mac-123.pdf",

"signedPodUrl": "https://storage.cloud.com/pods/signed-pod-mac-123.pdf",

"signedDcUrl": "https://storage.cloud.com/dcs/signed-dc-mac-123.pdf",

"signedDciSmartUrl": "https://storage.cloud.com/dcs/ismart-dc-mac-123.pdf",

"items": [

{

"productName": "Auto Scrubber",

"quantity": 1,

"landedPrice": 150000

}

]

}

]

}

**2. API to Submit Machinery GRN**

This API is called when the Requestor clicks "Create GRN" and submits the form. It is similar to a material GRN but has a unique mandatory requirement.

- **Endpoint:** POST /api/purchase-orders/machinery/{poNumber}/grn
- **Authorization:** Requestor role.
- **Request Format:** multipart/form-data
- **Request Payload:**  
    The request consists of a data field (JSON) and multiple file parts.

Same as material GRN with this one mandatory addition:

assetConditionProof-   photo of the delivered machine, unboxed, to verify its physical condition.

- **Backend Actions:**
    1. Upon successful submission, the backend updates the PO status to GRN_SUBMITTED.
    2. It should also create a new asset record in the master asset database with the details of the received machine.

**3. API for Document Downloads**

- **Generate Delivery Challan (Copy):** GET /api/purchase-orders/machinery/{poNumber}/dc-pdf
- **Export List to Excel:** GET /api/requestor/machinery-orders/export

# 36. API Specification: Vendor Machinery Invoice Upload

This section details the APIs enabling vendors to upload invoices for Machinery Purchase Orders that have a GRN SUBMITTED status.

**1. API to Fetch Machinery POs Ready for Invoicing**

This API populates the vendor's dashboard with all Machinery POs that are eligible for invoicing.

- **Endpoint:** GET /api/vendor/machinery-orders
- **Authorization:** Vendor role required.
- **Query Parameters:**
    - state (string, optional): Filters the POs by their delivery region/state (e.g., "Karnataka").
    - search (string, optional): A general search query matching PO Number or Site Name.
- **Success Response (200 OK):**  
    A JSON object containing the list of eligible POs, with all fields required by the UI.

{

"pagination": { "currentPage": 1, "totalPages": 3, "totalItems": 25 },

"orders": [

{

"id": "uuid-mac-123",

"poNumber": "PO-MAC-98765",

"poDate": "2023-11-10T12:00:00Z",

"vendorName": "Heavy Duty Equipments Ltd",

"siteName": "Site B - Bangalore Campus",

"region": "Karnataka",

"status": "GRN_SUBMITTED",

"deliveryType": "Courier",

"dateOfDelivery": "2023-11-16",

"podImageUrl": "https://storage.cloud.com/pods/pod-mac-123.pdf",

"signedDcUrl": "https://storage.cloud.com/dcs/signed-dc-mac-123.pdf",

"dcNumber": "DC-VENDOR-556",

"dcDate": "2023-11-15",

"tat": 7,

"courierName": "Delhivery",

"podNumber": "DEL987654321",

"expectedDeliveryDate": "2023-11-17",

"tatStatus": "Within TAT",

"reason": null,

"invoiceDetails": []

}

]

}

**2. API to Fetch Consolidated Items for Invoice Summary**

Called when the vendor selects multiple POs and clicks "Create Invoice". The API returns an aggregated list of all items from the selected POs to populate the summary modal.

- **Endpoint:** POST /api/purchase-orders/machinery/consolidated-items
- **Authorization:** Vendor role required.
- **Request Body:**

{

"poNumbers": ["PO-MAC-98765", "PO-MAC-98766"]

}

**Success Response (200 OK):**

{

"totalValue": 275000.00,

"items": [

{

"poNumber": "PO-MAC-98765",

"productName": "Auto Scrubber",

"quantity": 1,

"landedPrice": 150000

},

{

"poNumber": "PO-MAC-98766",

"productName": "High Pressure Jet",

"quantity": 2,

"landedPrice": 62500

}

]

}

**3. API to Upload Consolidated Machinery Invoice**

This is the main transaction API for submitting the invoice form. It links a single invoice document to multiple Machinery POs.(Same as materials PO invoice)

- **Endpoint:** POST /api/invoices/consolidated/machinery
- **Authorization:** Vendor role required.
- **Request Format:** multipart/form-data

**Request Payload:**  
**A. data (JSON String)**  

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|invoiceNo|String|Yes|The unique invoice number from the vendor.|
|state|String|Yes|The state/region this invoice applies to.|
|billAmount|Number|Yes|The total amount on the invoice document.|
|poNumbers|Array<String>|Yes|An array of PO Numbers covered by this invoice.|

**B. File Part**  

|   |   |   |
|---|---|---|
|**Field Name**|**Required**|**Validation**|
|billUpload|Yes|The invoice document (PDF/Image).|

**Backend Validation & Logic:**

- 1. The backend must verify that all poNumbers in the payload belong to the authenticated vendor and are in the GRN_SUBMITTED state.
    2. It should also confirm that all POs belong to the specified state.
    3. Upon successful validation, it updates the status of all linked POs to INVOICE_SUBMITTED.

**4. API for Document Viewing and Export**

- **View PO Details (Modal):** GET /api/purchase-orders/machinery/{poNumber}
- **Print PO:** GET /api/purchase-orders/machinery/{poNumber}/pdf
- **Export to Excel (All):** GET /api/vendor/machinery-orders/export-all

# 37. API Specification: Machinery Invoice Approval

This API provides the consolidated view of machinery invoices submitted by vendors. Since one invoice can cover multiple POs (Consolidated Invoice), the backend must aggregate the data into a single approval entry.

1. **Endpoint:** GET /api/invoices/machinery/approval-list
2. **Authorization:**
    - Roles: Procurement Head.
3. **Query Parameters:**
    - status (string, optional): Filter by "Pending", "Approved", or "Rejected".
    - site (string, optional): Filter by Site Name.
    - state (string, optional): Filter by State.
    - search (string, optional): Search by Invoice #, PO #, Vendor, or Site.
4. **Success Response (200 OK):**  
    A JSON object containing an array of consolidated invoices.

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 15 },

"invoices": [

{

"invoiceId": "INV-17098234",

"invoiceNo": "MAC/OCT/2023/045",

"invoiceDate": "2023-10-30T10:00:00Z",

"billAmount": 325000.00,

"state": "Karnataka",

"billUrl": "https://storage.cloud.com/invoices/Karnataka/mac-vendor-01.pdf",

"status": "Pending",

"poNumber": "PO-MAC-98765, PO-MAC-98766",

"vendorName": "Heavy Duty Equipments Ltd",

"siteName": "Multiple Sites",

"poDate": "2023-10-20T09:00:00Z",

"relatedPoNumbers": ["PO-MAC-98765", "PO-MAC-98766"],

"poItems": [

{

"productName": "Auto Scrubber",

"quantity": 1,

"landedPrice": 150000,

"rate": 150000,

"amount": 150000

}

],

"grnDetails": {

"comments": "PO-MAC-98765: Received in good condition. \nPO-MAC-98766: Small scratch on body.",

"signedDc": "https://storage.cloud.com/dcs/signed-dc-123.pdf",

"packagingImages": ["https://storage.cloud.com/grn/img1.jpg"],

"items": [

{

"itemName": "Auto Scrubber",

"orderedQuantity": 1,

"receivedQuantity": 1,

"isAccepted": true

}

]

}

}

]

}

# 38. API Specification: Approve Machinery Invoices

This endpoint handles the approval of one or more machinery invoices.

1. **Endpoint:** POST /api/invoices/machinery/approve
2. **Authorization:**
    - Roles: Procurement Head.
3. **Request Body (JSON):**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|invoiceIds|Array of Strings|Yes|List of IDs to be approved.|

**Example Payload:**

{

"invoiceIds": ["INV-17098234", "INV-17098235"]

}

1. **Business Logic:**
    - Change the status of the invoice records to Approved.
    - Update all linked Machinery Purchase Orders to a status reflecting financial approval (e.g., PAYMENT_PENDING).

# 39. API Specification: Reject Machinery Invoice

Used to reject a specific invoice with a reason.

1. **Endpoint:** POST /api/invoices/machinery/{invoiceId}/reject
2. **Authorization:**
    - Roles: Procurement Head.
3. **URL Parameter:**
    - {invoiceId} (string): The ID of the invoice to reject.

**Example Payload:**

{

"reason": "Invoice amount does not match the quantity received in GRN."

}

1. **Business Logic:**
    - Change invoice status to Rejected.
    - Update linked POs back to GRN_SUBMITTED so the vendor can re-upload a corrected invoice.
    - Trigger an email notification to the Vendor with the rejection reason.

# 40. API Specification: Fetch Machinery GRN Assets

This API specifically serves the files required by the GrnDetailsModal for machinery, including the mandatory Asset Condition photo.

1. **Endpoint:** GET /api/machinery/grn/{poNumber}/evidence
2. **Success Response (200 OK):**

{

"signedDcUrl": "https://storage.cloud.com/dcs/signed-dc-123.pdf",

"assetConditionPhotos": [

"https://storage.cloud.com/grn/machine-condition-01.jpg",

"https://storage.cloud.com/grn/machine-condition-02.jpg"

],

"packagingImages": [

"https://storage.cloud.com/grn/box-condition.jpg"

]

}

# 41. API Specification: Fetch Employees for Uniform Request

This API is used to populate the "Identify Employee" dropdown. It provides the necessary details to determine eligibility (last issuance date) and pre-fill the form.

1. **Endpoint:** GET /api/employees/uniform-search
2. **Authorization:**
    - Role: Site Manager.
3. **Query Parameters:**
    - q (string, optional): Search query for Name or Employee Code.
4. **Success Response (200 OK):**  
    A JSON array containing employee details.

[

{

"code": "EMP101",

"name": "Rahul Sharma",

"designation": "Housekeeper",

"gender": "Male",

"client": "Global Enterprises",

"site": "Site A",

"lastIssuanceDate": "2023-05-20"

},

{

"code": "EMP103",

"name": "Amit Kumar",

"designation": "Pantry Boy",

"gender": "Male",

"client": "Tech Solutions",

"site": "Site C",

"lastIssuanceDate": null

}

]

# 42. API Specification: Fetch Uniform Configuration

This API returns the list of uniform items available for a specific designation and their valid sizes.

1. **Endpoint:** GET /api/uniforms/configuration
2. **Authorization:**
    - Role: Site Manager.
3. **Query Parameters:**
    - designation (string, required): The designation of the selected employee (e.g., "Housekeeper", "Security").
    - gender (string, optional): To filter items/sizes by gender if applicable.
4. **Success Response (200 OK):**  
    A JSON object where keys are item names and values contain size options.

{

"items": [

{

"itemName": "Shirt",

"availableSizes": [

{ "value": "38", "label": "38 (S)" },

{ "value": "40", "label": "40 (M)" },

{ "value": "42", "label": "42 (L)" }

]

},

{

"itemName": "Pant",

"availableSizes": [

{ "value": "30", "label": "30" },

{ "value": "32", "label": "32" }

]

},

{

"itemName": "Shoes",

"availableSizes": [

{ "value": "7", "label": "7" },

{ "value": "8", "label": "8" }

]

}

]

}

# 43. API Specification: Submit Uniform Request

This API is called when the user clicks "Forward Request". It validates the request against business rules (e.g., 18-month policy) and creates a new transaction.

1. **Endpoint:** POST /api/uniform-requests
2. **Authorization:**
    - Role: Site Manager.
3. **Request Body:**  
    A JSON object with the following structure:

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|employeeCode|String|Yes|Unique ID of the employee receiving the uniform.|
|issueType|String|Yes|Type of request.|
|replacingEmployeeCode|String|Conditional|Required if issueType is "backfill".|
|justification|String|Conditional|Required if request is within 18 months of lastIssuanceDate.|
|items|Array of Objects|Yes|List of items being requested.|

**Structure of items Array Object:**

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|itemName|String|Yes|Name of the item (e.g., “Shirt”).|
|size|String|Yes|Selected size value.|
|quantity|Number|Yes|Must be greater than 0.|

**Example JSON Payload:**

{

"employeeCode": "EMP102",

"issueType": "backfill",

"replacingEmployeeCode": "EMP999",

"justification": null,

"items": [

{

"itemName": "Shirt",

"size": "40",

"quantity": 2

},

{

"itemName": "Shoes",

"size": "8",

"quantity": 1

}

]

}

**Allowed Values & Business Validation:**

- issueType: Must be one of ["new", "replacement", "backfill"].
- **18-Month Rule:** 
    - If today - lastIssuanceDate < 18 months AND issueType is "replacement":

justification field becomes Mandatory.

- **Quantity Check:** The backend must ensure the items array is not empty and contains at least one item with quantity > 0.
- **Backfill Check:** If issueType is "backfill", replacingEmployeeCode must be valid and exist in the system.

**Post-Processing (Backend Actions):**

- Generate a unique Request ID (e.g., UNF-12345).
- Set initial status to PENDING_PH_APPROVAL.

# 44. API Specification: Fetch Uniform Requests (Approval Dashboard)

This API populates the "Uniform Approvals" table. It allows the Procurement Head to view all pending requests.

1. **Endpoint:** GET /api/uniform-requests
2. **Authorization:**
    - Role: Procurement Head.
3. **Query Parameters:**
    - status (string, optional): Default to PENDING_PH_APPROVAL.
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.
4. **Success Response (200 OK):**  
    A JSON object containing the requests. The backend must attach the current stock level (availableStock) for each requested item so the UI can highlight shortages immediately.

{

"pagination": { "currentPage": 1, "totalPages": 5, "totalItems": 42 },

"requests": [

{

"id": "UNF-12345",

"employeeCode": "EMP101",

"employeeName": "Rahul Sharma",

"designation": "Housekeeper",

"site": "Site A",

"client": "Global Enterprises",

"issueType": "replacement",

"justification": "Old uniform torn during duty",

"requestDate": "2023-10-25T10:00:00Z",

"status": "PENDING_PH_APPROVAL",

"isEarlyReplacement": true,

"items": [

{

"itemName": "Shirt",

"size": "40",

"quantity": 2,

"availableStock": 2

},

{

"itemName": "Shoes",

"size": "8",

"quantity": 1,

"availableStock": 0

}

]

}

]

}

**Note:** isEarlyReplacement should be calculated by the backend if the request date is within 18 months of the last issue date, assisting the UI in displaying the warning badge.

# 45. API Specification: Fetch Employee Uniform History

This API is called when the user clicks the "History" tab in the modal. It shows previous uniforms issued to the specific employee.

1. **Endpoint:** GET /api/employees/{employeeCode}/uniform-history
2. **Authorization:**
    - Role: Procurement Head.
3. **URL Parameter:**
    - {employeeCode} (string, required): The ID of the employee.
4. **Success Response (200 OK):**

[

{

"date": "2023-05-20",

"type": "New Issue",

"items": "Shirt (2), Pant (2), Shoes (1)",

"status": "Issued"

},

{

"date": "2022-11-10",

"type": "Replacement",

"items": "Shoes (1)",

"status": "Issued"

}

]

# 46. API Specification: Fetch Uniform Vendors

This API populates the vendor dropdown in the modal when "Vendor" source is selected.

1. **Endpoint:** GET /api/vendors/category/uniforms
2. **Authorization:**
    - Role: Procurement Head.
3. **Success Response (200 OK):**

[

{ "value": "VEN-U01", "label": "V-Global Uniforms" },

{ "value": "VEN-U02", "label": "Style Textures Ltd" }

]

# 47. API Specification: Fulfil Uniform Request

This API is called when the Procurement Head clicks "Confirm Fulfilment". It handles the complex logic of splitting items between **Internal Stock deduction** and **Vendor Purchase Order creation**.

1. **Endpoint:** POST /api/uniform-requests/{requestId}/fulfill
2. **Authorization:**
    - Role: Procurement Head.
3. **Request Body:**  
    A JSON object defining how each item in the request is being fulfilled.

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|fulfillmentDetails|Array of Objects|Yes|List detailing the source for each requested item.|

1. **Structure of fulfillmentDetails Object:**

|   |   |   |   |
|---|---|---|---|
|**Field Name**|**Data Type**|**Required**|**Description**|
|itemName|String|Yes|Name of the item.|
|size|String|Yes|Size of the item.|
|quantity|Number|Yes|Quantity being processed.|
|source|String|Yes|Must be “stock” or “vendor”.|
|vendorId|String|Conditional|Required if source is “vendor”.|

1. **Example JSON Payload:**

{

"fulfillmentDetails": [

{

"itemName": "Shirt",

"size": "40",

"quantity": 2,

"source": "stock"

},

{

"itemName": "Shoes",

"size": "8",

"quantity": 1,

"source": "vendor",

"vendorId": "VEN-U01"

}

]

}

1. **Backend Business Logic:**
    - **Stock Items:**
        - Deduct quantity from the central inventory.
        - Create a "Stock Issue Log" record (Status: Issued).
    - **Vendor Items:**
        - Group items by vendorId.
        - Create a unique **Purchase Order (PO)** for each vendor (Status: Pending Delivery).
        - Fetch item prices from the master price list to calculate PO value.
    - **Request Status:** Update the main Uniform Request status to PROCESSED.
    - **Notifications:** Send email to Site Manger (Request Fulfilled) and relevant Vendors (New PO Received).

# 48. API Specification: Reject Uniform Request

This API is called when the Procurement Head rejects a request.

1. **Endpoint:** POST /api/uniform-requests/{requestId}/reject
2. **Authorization:**
    - Role: Procurement Head.
3. **Example JSON Payload:**

{

"reason": "Duplicate request. Employee already received uniform last month."

}

1. **Logic:**
    - Update request status to REJECTED.
    - Notify the requestor (Site Manager) via email.

# 49. API Specification: Uniform Purchase Order Management

This section details the APIs required to view, update, and generate documents (PDF/Excel) for Uniform Purchase Orders.

**1. API to Fetch Uniform Purchase Orders (List View)**

This API populates the main table with uniform-specific purchase orders. It supports search filtering matching the frontend's search bar.

- **Endpoint:** GET /api/purchase-orders/uniform
- **Authorization:** Vendor.
- **Query Parameters:**
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.
    - search (string, optional): Matches against Employee Name, PO Number, or Vendor Name.
- **Success Response (200 OK):**  
    A JSON object containing the list of POs.

{

"pagination": { "currentPage": 1, "totalPages": 5, "totalItems": 50 },

"orders": [

{

"id": "uuid-123",

"poNumber": "PO-UNF-87654",

"poDate": "2023-10-26T10:00:00Z",

"vendorName": "V-Global Uniforms",

"vendorId": "VEN-U01",

"employeeName": "Rahul Sharma",

"employeeCode": "EMP101",

"siteName": "Site A",

"region": "Maharashtra",

"status": "In Transit",

"deliveryType": "Courier",

"courierName": "BlueDart",

"tat": 5,

"tatStatus": "Within TAT",

"expectedDeliveryDate": "2023-10-31",

"podImageUrl": "https://storage.cloud.com/pod/pod-123.pdf",

"signedPodUrl": null,

"signedDcUrl": null,

"items": [

{

"productName": "Shirt",

"size": "40",

"quantity": 2,

"landedPrice": 450

}

]

}

]

}

**2. API to Fetch Single PO Details**

Used to populate the "View" modal.

- **Endpoint:** GET /api/purchase-orders/uniform/{poNumber}
- **Authorization:** Vendor role required.
- **Success Response (200 OK):** Returns the full UniformPurchaseOrder object (structure same as list item above, but guaranteed to contain full item details).

**3. API to Update Uniform Purchase Order**

Used when the "Edit" modal is submitted.

- **Endpoint:** PUT /api/purchase-orders/uniform/{poNumber}
- **Authorization:** Vendor role required.
- **Request Body & Behavior:**
    - **Note:** The Request Body structure, validation rules, and editable fields (e.g., Status, Courier Details, Delivery Date, Document Uploads) are identical to the **Material Purchase Order Update API** documented previously.
    - Please refer to the _Material PO Edit Specification_ for the field definitions (e.g., deliveryType, courierName, podImage upload, etc.).

**4. API to Download/Export Documents**

These endpoints handle the generation of specific files triggered by the action buttons in the table.

**A. Generate PO PDF**

- **Trigger:** Click on "Print"
- **Endpoint:** GET /api/purchase-orders/uniform/{poNumber}/pdf
- **Response:** Binary file (application/pdf) containing the formatted Purchase Order.

**B. Generate Delivery Challan (DC)**

- **Trigger:** Click on "DC"
- **Endpoint:** GET /api/purchase-orders/uniform/{poNumber}/dc-pdf
- **Response:** Binary file (application/pdf) containing the Delivery Challan details for the vendor.

**C. Export Single PO to Excel**

- **Trigger:** Click on "Excel”
- **Endpoint:** GET /api/purchase-orders/uniform/{poNumber}/export
- **Response:** Binary file (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet).

**D. Export All POs to Excel**

- **Trigger:** Click on "Export All to Excel" button
- **Endpoint:** GET /api/purchase-orders/uniform/export-all
- **Query Parameters:** Should accept the same search parameters as the List API to export the currently filtered view.
- **Response:** Binary file (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet) containing the full dataset.

# 50. API Specification: Requestor Uniform PO Management

This section details the APIs for the Requestor to view their site's uniform orders and acknowledge receipt.

**1. API to Fetch My Uniform Orders**

This API populates the main table.

- **Endpoint:** GET /api/requestor/uniform-orders
- **Authorization:** Requestor.
- **Query Parameters:**
    - page (number, optional)
    - limit (number, optional)
    - search (string, optional): Matches PO Number, Employee Name, or Vendor.
- **Success Response (200 OK):**  
    A JSON object containing the list.

**Required JSON Structure:**

{

"pagination": { "currentPage": 1, "totalPages": 10, "totalItems": 100 },

"orders": [

{

"id": "uuid-12345",

"poNumber": "PO-UNF-87654",

"poDate": "2023-10-26T10:00:00Z",

"vendorName": "V-Global Uniforms",

"vendorId": "VEN-U01",

"employeeName": "Rahul Sharma",

"employeeCode": "EMP101",

"siteName": "Site A",

"region": "Maharashtra",

"status": "Delivered",

"deliveryType": "Courier",

"courierName": "BlueDart",

"podNumber": "BD123456",

"dcNumber": "DC-998877",

"dcDate": "2023-10-27",

"tat": 4,

"tatStatus": "Within TAT",

"expectedDeliveryDate": "2023-10-30",

"dateOfDelivery": "2023-10-29",

"reason": null,

"podImageUrl": "https://storage.cloud.com/pods/pod-123.pdf",

"signedPodUrl": "https://storage.cloud.com/pods/signed-pod-123.pdf",

"signedDcUrl": "https://storage.cloud.com/dcs/signed-dc-123.pdf",

"signedDciSmartUrl": "https://storage.cloud.com/dcs/ismart-dc-123.pdf",

"items": [

{

"productName": "Shirt",

"size": "40",

"quantity": 2,

"landedPrice": 450

}

]

}

]

}

**2. API to Submit Uniform GRN (Goods Reception Note)**

This API is called when the Requestor clicks **"**Create GRN".

- **Endpoint:** POST /api/purchase-orders/uniform/{poNumber}/grn
- **Authorization:** Requestor role.
- **Request Format:** multipart/form-data
- **Mandatory Requirement:** Same as Material GRNs, addition: Uniform GRNs must include a "Proof of Deployment" (Employee Photo).

**3. API to Generate Requestor Documents**

- **Delivery Challan (Print):** GET /api/purchase-orders/uniform/{poNumber}/dc-pdf
- **Export to Excel:** GET /api/requestor/uniform-orders/export

# 51. API Specification: Vendor Uniform Invoice Upload

This section details the workflow for Vendors to upload invoices for Uniform POs where the Goods Reception Note (GRN) has been submitted.

**1. API to Fetch POs Ready for Invoicing**

This API populates the main table. It should return Uniform POs that have been delivered and have a submitted GRN.

- **Endpoint:** GET /api/vendor/uniform-orders
- **Authorization:** Vendor role required.
- **Query Parameters:**
    - state (string, optional): To filter by Region/State (e.g., "Maharashtra").
    - search (string, optional): Matches PO Number, Employee Name, or Site.
- **Success Response (200 OK):**  
    A JSON object containing the list of POs.

{

"pagination": { "currentPage": 1, "totalPages": 5, "totalItems": 45 },

"orders": [

{

"id": "uuid-101",

"poNumber": "PO-UNF-87654",

"poDate": "2023-10-26T10:00:00Z",

"vendorName": "V-Global Uniforms",

"employeeName": "Rahul Sharma",

"employeeCode": "EMP101",

"siteName": "Site A",

"region": "Maharashtra",

"status": "GRN_SUBMITTED",

"deliveryType": "Courier",

"dateOfDelivery": "2023-10-29",

"podImageUrl": "https://storage.cloud.com/pod/123.pdf",

"signedPodUrl": "https://storage.cloud.com/pod/signed-123.pdf",

"signedDcUrl": "https://storage.cloud.com/dc/signed-123.pdf",

"dcNumber": "DC-9988",

"dcDate": "2023-10-27",

"tat": 4,

"courierName": "BlueDart",

"podNumber": "BD123456",

"expectedDeliveryDate": "2023-10-30",

"invoiceDetails": []

}

]

}

**2. API to Fetch Consolidated Items (Summary Modal)**

Called when the user selects multiple POs and clicks "Create Invoice". It returns the specific line items for the selected PO IDs to calculate the total value displayed in the modal.

- **Endpoint:** POST /api/purchase-orders/uniform/consolidated-items
- **Authorization:** Vendor role required.
- **Request Body:**

{

"poNumbers": ["PO-UNF-87654", "PO-UNF-87655"]

}

- **Success Response (200 OK):**

{

"totalValue": 2500.00,

"items": [

{

"poNumber": "PO-UNF-87654",

"productName": "Shirt",

"size": "40",

"quantity": 2,

"landedPrice": 450

},

{

"poNumber": "PO-UNF-87655",

"productName": "Shoes",

"size": "8",

"quantity": 1,

"landedPrice": 1600

}

]

}

**3. API to Upload Consolidated Invoice**

This API is called when the invoice form in the modal is submitted. It links a single invoice document to multiple PO numbers.

- **Endpoint:** POST /api/invoices/consolidated
- **Authorization:** Vendor role required.
- **Request Format:** multipart/form-data
- **Request Payload:**  
    **A. data (JSON String)**

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|invoiceNo|String|Yes|The vendor’s invoice number.|
|state|String|Yes|The state this invoice belongs to (e.g., “Maharashtra”).|
|billAmount|Number|Yes|Total amount on the invoice.|
|poNumbers|Array<String>|Yes|List of PO Numbers this invoice covers.|

  
**B. File Part**  

|   |   |   |
|---|---|---|
|**Field Name**|**Required**|**Validation**|
|billUpload|Yes|PDF/Image of the invoice. Max 5MB.|

- **Backend Validation Logic:**
    1. Verify all poNumbers belong to the authenticated Vendor.
    2. Verify all poNumbers belong to the state provided in the payload.
    3. Verify all poNumbers are currently in a state allowing invoicing (e.g., GRN_SUBMITTED).
    4. Update the status of these POs to INVOICE_SUBMITTED.
- **Example Payload:**

Content-Disposition: form-data; name="data"

{

"invoiceNo": "INV-2023-001",

"invoiceDate": "2023-11-01",

"state": "Maharashtra",

"billAmount": 2500,

"poNumbers": ["PO-UNF-87654", "PO-UNF-87655"]

}

Content-Disposition: form-data; name="billUpload"; filename="invoice.pdf"

**4. API to View PO Details (Modal)**

Called when the View Modal is opened.

- **Endpoint:** GET /api/purchase-orders/uniform/{poNumber}
- **Success Response:** Returns full PO details including line items.

**5. API to Export/Print**

- **Export to Excel:** GET /api/vendor/uniform-orders/export
- **Print PO:** GET /api/purchase-orders/uniform/{poNumber}/pdf

# 52. API Specification: Uniform Invoice Approval

This section covers the APIs for the procurement team to review, approve, or reject vendor-submitted invoices for uniform deliveries.

**1. API to Fetch Invoices for Approval**

This is the main API that populates the approval dashboard. The backend is responsible for finding all POs with submitted invoices, grouping them by invoice ID, and aggregating the data from all related POs into a single, comprehensive object for each invoice.

- **Endpoint:** GET /api/invoices/uniform/approval-list
- **Authorization:** Procurement Head role required.
- **Query Parameters:**
    - state (string, optional): Filter by state/region.
    - site (string, optional): Filter by site name.
    - search (string, optional): Searches against Invoice #, Vendor Name, PO Number(s), or Recipient Name.
- **Success Response (200 OK):**  
    A JSON object containing an array of consolidated invoice objects.

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 18 },

"invoices": [

{

"invoiceId": "INV-UNF-12345",

"invoiceNo": "VENDOR-ABC-001",

"invoiceDate": "2023-11-05T10:00:00Z",

"billAmount": 12500.00,

"state": "Maharashtra",

"billUrl": "https://storage.cloud.com/invoices/vendor-abc-001.pdf",

"status": "Pending",

"poNumbersDisplay": "PO-UNF-101, PO-UNF-102",

"vendorName": "V-Global Uniforms",

"siteName": "Multiple Sites",

"recipientDisplay": "2 Recipients",

"poDate": "2023-10-28T09:00:00Z",

"relatedPoNumbers": ["PO-UNF-101", "PO-UNF-102"],

"poItems": [

{ "productName": "Shirt (40)", "quantity": 10, "rate": 450, "amount": 4500 },

{ "productName": "Shoes (8)", "quantity": 10, "rate": 800, "amount": 8000 }

],

"grnDetails": {

"comments": "PO-UNF-101: Received well. \nPO-UNF-102: Box was slightly damaged but items are fine.",

"signedDcUrl": "https://storage.cloud.com/grn/dc-scan-101.pdf",

"packagingImageUrls": [

"https://storage.cloud.com/grn/pkg-1.jpg",

"https://storage.cloud.com/grn/pkg-2.jpg"

],

"items": [

{ "itemName": "Shirt (40)", "orderedQuantity": 10, "receivedQuantity": 10, "isAccepted": true },

{ "itemName": "Shoes (8)", "orderedQuantity": 10, "receivedQuantity": 10, "isAccepted": true }

]

}

}

]

}

**Backend Aggregation Logic:**

- - For each unique invoice ID, the backend must find all linked POs.
    - poNumbersDisplay: A comma-separated string of all linked PO numbers.
    - recipientDisplay: A descriptive name (e.g., "Rahul Sharma" if one PO, "3 Recipients" if multiple).
    - poItems: A combined list of all line items from all linked POs.
    - grnDetails: A consolidated object combining data from the GRNs of all linked POs.

**2. API for Invoice Actions (Approve / Reject)**

This single endpoint handles status changes for one or more invoices.

- **Endpoint:** POST /api/invoices/uniform/process-actions
- **Authorization:**  Procurement Head role required.
- **Request Body:**  
    A JSON object detailing the invoices to action.

|   |   |   |   |
|---|---|---|---|
|**Field**|**Type**|**Required**|**Description**|
|action|String|Yes|Must be "APPROVE" or "REJECT".|
|invoiceIds|Array of Strings|Yes|An array of one or more invoiceIds to process.|
|reason|String|Conditional|Required if action is "REJECT".|

- **Example Payload (Bulk Approve):**

{

"action": "APPROVE",

"invoiceIds": ["INV-UNF-12345", "INV-UNF-12346"]

}

- **Example Payload (Single Reject):**

{

"action": "REJECT",

"invoiceIds": ["INV-UNF-12347"],

"reason": "Invoice amount exceeds the value of goods received in GRN."

}

**3. API to Serve Documents**

These endpoints provide the binary data for viewing bills and GRN evidence. They should return the file with the appropriate Content-Type header (e.g., application/pdf, image/jpeg).

- **View Invoice Bill:** GET /api/documents/invoice/{invoiceId}
- **View Signed DC:** GET /api/documents/grn/{poNumber}/signed-dc
- **View Packaging Image:** GET /api/documents/grn/images/{imageId}

# 53. API Specification: Fetch Internal Uniform Allocations

This API populates the table showing uniforms issued from the central/internal warehouse to specific employees at the requestor's site.

1. **Endpoint:** GET /api/uniform-stock/issues
2. **Authorization:**
    - Roles: Requestor.
3. **Query Parameters:**
    - page (number, optional): For pagination.
    - limit (number, optional): For pagination.
4. **Success Response (200 OK):**  
    A JSON object containing the list of internal issue records.

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 12 },

"issues": [

{

"issueId": "ISS-1712345678",

"issueDate": "2023-11-01T10:00:00Z",

"site": "Site A - Mumbai HQ",

"employeeName": "Rahul Sharma",

"employeeCode": "EMP101",

"requestId": "UNF-88776",

"status": "ISSUED",

"items": [

{

"itemName": "Shirt",

"size": "40",

"quantity": 2

},

{

"itemName": "Pant",

"size": "32",

"quantity": 2

}

]

}

]

}

# 54. API Specification: Mark Uniform Allocation as Received

This API is called when the Requestor clicks the "Mark Received" button, confirming that the employee has physically received the items issued from stock.

1. **Endpoint:** PATCH /api/uniform-stock/issues/{issueId}/receive
2. **Authorization:**
    - Roles: Requestor.
3. **URL Parameter:**
    - {issueId} (string): The unique ID of the stock issue record.
4. **Success Response (200 OK):**

{

"issueId": "ISS-1712345678",

"status": "RECEIVED"

}

1. **Business Logic:**
    - Updates the status of the issue record to RECEIVED.
    - This action acts as the "Internal GRN" for stock-fulfilled items.

# 55. API Specification: Download Uniform Issue Slip

This API generates the PDF "Gate Pass" or "Issue Slip" for the allocation, used for security documentation when items leave the stock area or are handed over.

1. **Endpoint:** GET /api/uniform-stock/issues/{issueId}/slip
2. **Authorization:**
    - Roles: Requestor.
3. **URL Parameter:**
    - {issueId} (string): The unique ID of the issue record.
4. **Response:**
    - **Content-Type:** application/pdf
    - **Description:** A binary PDF file containing the Employee details, Item breakdown, etc.

# 56. API Specification: Fetch Machinery Transfers

This API populates the table for both Incoming and Outgoing transfers based on the user's site context and selected tab.

1. **Endpoint:** GET /api/machinery-transfers
2. **Authorization:**
    - Roles: Site Manager.
3. **Query Parameters:**
    - siteId (string, required): The ID of the site the user is currently managing.
    - direction (string, required): Must be incoming (where targetSite = siteId) or outgoing (where sourceSite = siteId).
    - search (string, optional): Search by Transfer ID, Machine Name, or Serial Number.
    - page / limit (number, optional): For pagination.
4. **Success Response (200 OK):**

{

"pagination": { "currentPage": 1, "totalPages": 2, "totalItems": 10 },

"transfers": [

{

"transferId": "TRF-171550123",

"date": "2023-11-12T08:30:00Z",

"status": "PENDING_DISPATCH",

"requestInfo": {

"id": "MREQ-55432",

"targetSite": "Site B - Bangalore"

},

"items": [

{

"machineName": "Single Disc Scrubber",

"quantity": 1,

"sourceSite": "Site A - Mumbai",

"serial": "MAC-SDS-004"

}

]

}

]

}

# 57. API Specification: Dispatch Machinery (Generate Gate Pass)

This API is called by the Source Site Manager to confirm the machine has left the premises.

1. **Endpoint:** POST /api/machinery-transfers/{transferId}/dispatch
2. **Authorization:** Site Manager of the Source Site.
3. **URL Parameter:**
    - {transferId} (string): The unique ID of the transfer record.
4. **Success Response (200 OK):**

{

"status": "IN_TRANSIT"

}

1. **Business Logic:**
    - Updates the status from PENDING_DISPATCH to IN_TRANSIT.
    - Generates a digital Gate Pass record.
    - Notifies the Target Site Manager that the asset is on the way.

# 58. API Specification: Receive Machinery

This API is called by the Target Site Manager to confirm the machinery has arrived and is in good condition.

1. **Endpoint:** POST /api/machinery-transfers/{transferId}/receive
2. **Authorization:** Site Manager of the Target Site.
3. **URL Parameter:**
    - {transferId} (string): The unique ID of the transfer record.
4. **Success Response (200 OK):**

{

"status": "RECEIVED"

}

1. **Business Logic:**
    - Updates status from IN_TRANSIT to RECEIVED.
    - **Registry Update:** The backend must automatically update the asset's location in the Master Asset DB from the Source Site to the Target Site.

# 59. API Specification: Download Transfer Gate Pass

Provides the PDF document required for security and logistics during the transfer.

1. **Endpoint:** GET /api/machinery-transfers/{transferId}/gate-pass
2. **Authorization:** Site Manager (Source or Target).
3. **Response:**
    - **Content-Type:** application/pdf
    - **Logic:** Returns a binary PDF containing the Transfer ID, Source Site, Destination Site, Asset Serial Numbers, and authorization stamps.