# NeoStats — Document Intelligence System

## 1. Project Overview

**NeoStats** is an AI-powered document intelligence application that processes financial documents and extracts structured information from:

* Invoices
* Balance Sheets
* Profit & Loss Statements
* Cash Flow Statements

The system validates uploaded documents, performs text extraction/OCR, uses an LLM for structured extraction, applies deterministic financial validations, persists results, and exposes them through a REST API and web dashboard.

### Processing Flow

```text
User Upload
    ↓
Document Validation
    ↓
PDF Text Extraction / OCR
    ↓
AI Structured Extraction
    ↓
Pydantic Validation
    ↓
Financial Validation
    ↓
PostgreSQL Persistence
    ↓
REST API Response
    ↓
Frontend Dashboard
```

---

# 2. Technology Stack

| Component       | Technology       |
| --------------- | ---------------- |
| Frontend        | React            |
| Backend         | Python + FastAPI |
| PDF Processing  | PyMuPDF          |
| OCR             | Tesseract        |
| AI Extraction   | Gemini API       |
| Structured Data | Pydantic         |
| Database        | PostgreSQL       |
| Database Layer  | SQLAlchemy       |
| Testing         | pytest           |
| Deployment      | Render           |

The architecture follows separation of concerns between API, services, validation, extraction, persistence, and utilities. 

---

# 3. Live Deliverables

| Deliverable           | URL                                      |
| --------------------- | ---------------------------------------- |
| **GitHub Repository** | `https://github.com/Satish-Dewasi/Intelligent-Document-Extraction`                        |
| **Live Frontend**     | `https://neostats-frontend.onrender.com/` |
| **Live Backend API**  | `https://neostats-backend-z89y.onrender.com/docs`                       |

---

# 4. API

### Process Document

```http
POST /api/v1/documents/process
```

Accepts:

* PDF
* JPG
* PNG
* Document type
* Uploaded file

### Get Document

```http
GET /api/v1/documents/{document_name}
```

### List Documents

```http
GET /api/v1/documents
```

### Health

```http
GET /api/v1/health
```

Swagger provides interactive API documentation. The required API endpoints and health endpoint are part of the case-study requirements. 

---

# 5. Architecture

```text
┌─────────────────┐
│ React Frontend  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│ FastAPI REST API│
└────────┬────────┘
         ▼
┌─────────────────┐
│ Document Service│
└────────┬────────┘
         │
   ┌─────┼──────────────┐
   ▼     ▼              ▼
Validation OCR      AI Extraction
Service   Service       Service
   │       │              │
   └───────┴──────┬───────┘
                  ▼
           Structured Result
                  │
                  ▼
        Financial Validation
                  │
                  ▼
          Document Repository
                  │
                  ▼
             PostgreSQL
```

---

# 6. Extraction & Validation

The AI layer extracts document information into structured JSON/Pydantic models.

Important design principle:

> **AI extracts; deterministic Python logic validates financial calculations.**

Missing information is represented as `null` rather than being invented. Tables and invoice line items are represented as structured arrays/objects. 

Financial validation supports document-specific reconciliation and returns statuses such as:

```text
PASS
FAIL
NOT_APPLICABLE
```

`NOT_APPLICABLE` is used when required information for a validation rule is unavailable. 

---

# 7. Sample JSON Output

### Invoice

{
  "message": "Document processed successfully.",
  "validation": {
    "valid": true,
    "status": "VALID",
    "file_type": "jpg",
    "page_count": null,
    "error_code": null,
    "message": null
  },
  "text_extraction": {
    "pages": [
      {
        "page_number": 1,
        "text": "Thank You. Flease came again.\nGoods Sold. Are Not Returnatle.\nFor’feedback or complaint, please call:\n\nF M11-3194 0284\n¥REDEEH VOUCHER BEFORE POINTS EXPIRY!\n\nSegi Cash & Carry Sdn. Bhd\n(317041-W)\nPT17920, SEKSYEN U9,\n40150 SHAH ALAK,\nSELANGOR TARUL EHSAN.\nGST Reg. No. + 001951645696\n\nTnvoice No\n\n2 47735\nliste : 04 Jan 2017 01:15pm\n: 03\n\nCounter\n\nUNICA PAIL 66L 600\n\ntx 17.44 i744 5\nHASSIHO FINE WHOLEMEAL 4206\nix 2.64 2.44 Z\n\nNo of items: 2\nTotal Incl. GS7:RM 2\nCash:RM 20.00\nChange: RH 2?\nMissed Point Today: 19\nServed by SITI SUHAINA BT OTHMAN\n\nSRERERERRENRE GST Summary REROORRREARE\n\nGST Code Amount(RM) Tax(RH)}\n§ @6.0% 146.42 0.99\nZ @0.04 2.64 0.00\n\nRRR RAR RAE R RE ARERR RT AAA RADAR ER EEA ARR\n\nRef No: 00600676213047735\nThank You. Please come again.\nGoods Sold Are Not Returnatle.\nFor feedback or complaint, please call:\n",
        "extraction_method": "ocr"
      }
    ]
  },
  "structured_extraction": {
    "document_type": "invoice",
    "fields": [
      {
        "name": "vendor_name",
        "value": {
          "text": "Segi Cash & Carry Sdn. Bhd",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Segi Cash & Carry Sdn. Bhd",
        "confidence": 0.95
      },
      {
        "name": "vendor_company_number",
        "value": {
          "text": "317041-W",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "(317041-W)",
        "confidence": 0.95
      },
      {
        "name": "vendor_address",
        "value": {
          "text": "PT17920, SEKSYEN U9, 40150 SHAH ALAK, SELANGOR TARUL EHSAN.",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "PT17920, SEKSYEN U9,\n40150 SHAH ALAK,\nSELANGOR TARUL EHSAN.",
        "confidence": 0.9
      },
      {
        "name": "vendor_gst_registration_number",
        "value": {
          "text": "001951645696",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "GST Reg. No. + 001951645696",
        "confidence": 0.95
      },
      {
        "name": "invoice_number",
        "value": {
          "text": "2 47735",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Tnvoice No\n\n2 47735",
        "confidence": 0.85
      },
      {
        "name": "invoice_date",
        "value": {
          "text": "04 Jan 2017",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "liste : 04 Jan 2017",
        "confidence": 0.8
      },
      {
        "name": "invoice_time",
        "value": {
          "text": "01:15pm",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "01:15pm",
        "confidence": 0.95
      },
      {
        "name": "counter",
        "value": {
          "text": "03",
          "number": 3,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Counter\n\n: 03",
        "confidence": 0.9
      },
      {
        "name": "number_of_items",
        "value": {
          "text": "2",
          "number": 2,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "No of items: 2",
        "confidence": 0.95
      },
      {
        "name": "total_including_gst",
        "value": {
          "text": "RM 2",
          "number": 2,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Total Incl. GS7:RM 2",
        "confidence": 0.8
      },
      {
        "name": "cash_payment",
        "value": {
          "text": "RM 20.00",
          "number": 20,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Cash:RM 20.00",
        "confidence": 0.95
      },
      {
        "name": "change",
        "value": {
          "text": "RH 2?",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Change: RH 2?",
        "confidence": 0.75
      },
      {
        "name": "missed_point_today",
        "value": {
          "text": "19",
          "number": 19,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Missed Point Today: 19",
        "confidence": 0.95
      },
      {
        "name": "cashier",
        "value": {
          "text": "SITI SUHAINA BT OTHMAN",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Served by SITI SUHAINA BT OTHMAN",
        "confidence": 0.95
      },
      {
        "name": "reference_number",
        "value": {
          "text": "00600676213047735",
          "number": null,
          "boolean": null
        },
        "page_number": 1,
        "evidence": "Ref No: 00600676213047735",
        "confidence": 0.95
      }
    ],
    "tables": [
      {
        "name": "line_items",
        "columns": [
          "Description",
          "Quantity",
          "Unit Price",
          "Amount",
          "Tax Code"
        ],
        "rows": [
          [
            "UNICA PAIL 66L 600",
            "1x",
            "17.44",
            "17.44",
            "5"
          ],
          [
            "HASSIHO FINE WHOLEMEAL 4206",
            "ix",
            "2.64",
            "2.44",
            "Z"
          ]
        ],
        "page_number": 1
      },
      {
        "name": "gst_summary",
        "columns": [
          "GST Code",
          "Amount(RM)",
          "Tax(RM)"
        ],
        "rows": [
          [
            "S @6.0%",
            "146.42",
            "0.99"
          ],
          [
            "Z @0.0%",
            "2.64",
            "0.00"
          ]
        ],
        "page_number": 1
      }
    ]
  },
  "financial_validation": {
    "checks": [
      {
        "name": "invoice_subtotal_check",
        "formula": "sum(line totals)",
        "operands": {},
        "calculated_value": null,
        "reported_value": null,
        "variance": null,
        "status": "NOT_APPLICABLE"
      },
      {
        "name": "invoice_total_check",
        "formula": "subtotal + tax - discount",
        "operands": {},
        "calculated_value": null,
        "reported_value": null,
        "variance": null,
        "status": "NOT_APPLICABLE"
      },
      {
        "name": "invoice_change_check",
        "formula": "cash paid - total",
        "operands": {},
        "calculated_value": null,
        "reported_value": null,
        "variance": null,
        "status": "NOT_APPLICABLE"
      }
    ]
  },
  "processing_time_ms": 46965.41442791931
}

---

# 8. AI / Tool Usage Declaration

AI tools were used transparently during development for:

* Architecture brainstorming
* Technical research and clarification
* Code assistance
* Debugging
* Test-case generation
* Code review
* Documentation assistance

The application itself uses **Gemini API** for document information extraction.

Financial calculations and validation rules are implemented deterministically in Python rather than delegated to the LLM.

---

# 9. Known Limitations & Production Improvements

### Current limitations

* OCR accuracy depends on document image quality.
* Highly unusual document layouts may reduce extraction accuracy.
* LLM extraction can require additional prompt/schema refinement for uncommon formats.
* Processing time depends partly on external AI/OCR services.
* Current deployment uses free-tier infrastructure.

### Future improvements

* Add asynchronous/background document processing.
* Add stronger OCR/layout detection.
* Add confidence scoring and human-review workflows.
* Add authentication and role-based access.
* Add object storage for original documents.
* Add retry/circuit-breaker handling for external AI services.
* Add monitoring, metrics and distributed tracing.
* Add more financial reconciliation rules and document templates.

---

# 10. Security & Configuration

Secrets/API keys are **not committed to GitHub**.

Configuration is supplied through environment variables.

Example:

```env
DATABASE_URL=...
GEMINI_API_KEY=...
```

The application also implements validation, logging, exception handling and modular service separation as required by the case study. 

---

# 11. Repository Structure

```text
neostats/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── utils/
│   └── tests/
│
├── frontend/
├── docs/
│   ├── architecture.png
│   └── solution_presentation.pdf
│
├── sample_outputs/
├── .env.example
├── .gitignore
└── README.md
```


---
