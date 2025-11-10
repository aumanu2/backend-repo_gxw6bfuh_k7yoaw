import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List
from database import create_document, get_documents

app = FastAPI(title="Startup Lawyer API", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Startup Lawyer API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------- Feature-specific endpoints (declare BEFORE dynamic routes) ----------

@app.get("/api/templates/defaults")
def default_templates():
    # A few starter templates with variables
    return [
        {
            "name": "Mutual NDA",
            "category": "contract",
            "variables": ["party_a_name", "party_b_name", "effective_date", "jurisdiction"],
            "body": (
                "This Mutual Non-Disclosure Agreement (the \"Agreement\") is made effective on {effective_date} between {party_a_name} and {party_b_name}. "
                "Each party agrees to hold Confidential Information in strict confidence and not to disclose it to any third party... Governing law: {jurisdiction}."
            )
        },
        {
            "name": "Advisor Agreement",
            "category": "corporate",
            "variables": ["company_name", "advisor_name", "equity_percent", "vesting_months"],
            "body": (
                "This Advisor Agreement is entered into by and between {company_name} and {advisor_name}. "
                "Compensation shall be equity equal to {equity_percent}% vesting over {vesting_months} months..."
            )
        },
        {
            "name": "IP Assignment",
            "category": "ip",
            "variables": ["assignor_name", "assignee_company", "effective_date"],
            "body": (
                "For good and valuable consideration, {assignor_name} hereby assigns to {assignee_company} all right, title, and interest in and to the Assigned Inventions effective {effective_date}..."
            )
        }
    ]

class GeneratePayload(BaseModel):
    template: Dict[str, Any]
    variables: Dict[str, Any]

@app.post("/api/generate")
def generate_document(payload: GeneratePayload):
    """Simple server-side merge of variables into a template body, persisted as a document"""
    try:
        template = payload.template
        variables = payload.variables
        body = template.get("body", "")
        filled = body.format(**variables)
        doc = {
            "title": template.get("name", "Generated Document"),
            "category": template.get("category", "contract"),
            "content": filled,
            "template_id": None,
            "variables": variables
        }
        new_id = create_document("document", doc)
        return {"id": new_id, "content": filled}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing variable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------- Generic CRUD routes (moved under a distinct prefix to avoid conflicts) ----------

class CreatePayload(BaseModel):
    data: Dict[str, Any]

@app.post("/api/collections/{collection}")
def create_item(collection: str, payload: CreatePayload):
    try:
        new_id = create_document(collection, payload.data)
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/collections/{collection}")
def list_items(collection: str, limit: int = 50):
    try:
        docs = get_documents(collection, limit=limit)
        # Convert ObjectId to string where present
        result: List[Dict[str, Any]] = []
        for d in docs:
            d["_id"] = str(d.get("_id"))
            result.append(d)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Optional: expose schemas overview for tooling/inspection
@app.get("/schema")
def schema_overview():
    try:
        from schemas import Client, Matter, DocumentTemplate, Document, Task
        def model_info(model):
            fields = {}
            for name, field in model.model_fields.items():  # type: ignore[attr-defined]
                fields[name] = str(field.annotation)
            return {"name": model.__name__.lower(), "fields": fields}
        return {
            "collections": [
                model_info(Client),
                model_info(Matter),
                model_info(DocumentTemplate),
                model_info(Document),
                model_info(Task),
            ]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
