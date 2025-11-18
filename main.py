import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Quote, Booking

app = FastAPI(title="Lawn Mowing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to convert Mongo docs

def serialize_doc(doc: Dict):
    if not doc:
        return doc
    d = {**doc}
    if isinstance(d.get("_id"), ObjectId):
        d["id"] = str(d.pop("_id"))
    # Convert datetime to isoformat
    for k, v in list(d.items()):
        try:
            import datetime
            if isinstance(v, (datetime.datetime, datetime.date)):
                d[k] = v.isoformat()
        except Exception:
            pass
    return d

@app.get("/")
def read_root():
    return {"message": "Lawn Mowing Backend is running"}

class QuoteInput(BaseModel):
    name: str
    email: str
    address: str
    zip_code: str
    lawn_size_sqft: int
    frequency: str  # once | biweekly | weekly
    extras: List[str] = []

EXTRA_PRICES = {
    "edging": 10.0,
    "leaf_cleanup": 20.0,
    "pet_waste": 8.0,
}

FREQUENCY_DISCOUNT = {
    "once": 0.0,
    "biweekly": 0.05,
    "weekly": 0.10,
}

SERVICE_FEE = 3.99


def calculate_price(lawn_size_sqft: int, frequency: str, extras: List[str]):
    # Base: $0.02 per sqft, minimum $30
    base = max(30.0, lawn_size_sqft * 0.02)
    extras_total = sum(EXTRA_PRICES.get(e, 0) for e in extras)
    discount = base * FREQUENCY_DISCOUNT.get(frequency, 0)
    total = base - discount + extras_total + SERVICE_FEE
    return base, extras_total, discount, total


@app.post("/api/quote")
def create_quote(q: QuoteInput):
    base, extras_total, discount, total = calculate_price(q.lawn_size_sqft, q.frequency, q.extras)
    quote_doc = Quote(
        name=q.name,
        email=q.email,
        address=q.address,
        zip_code=q.zip_code,
        lawn_size_sqft=q.lawn_size_sqft,
        frequency=q.frequency,
        extras=q.extras,
        base_price=base,
        discount=discount,
        extras_total=extras_total,
        service_fee=SERVICE_FEE,
        total=total,
    )
    try:
        quote_id = create_document("quote", quote_doc)
        return {"id": quote_id, **quote_doc.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quotes")
def list_quotes(limit: int = 50):
    try:
        docs = get_documents("quote", {}, limit)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BookingInput(BaseModel):
    quote_id: Optional[str] = None
    name: str
    email: str
    phone: str
    address: str
    zip_code: str
    lawn_size_sqft: int
    frequency: str
    extras: List[str] = []
    notes: Optional[str] = None
    preferred_date: Optional[str] = None  # iso date
    price_total: float


@app.post("/api/book")
def create_booking(b: BookingInput):
    # Trust price from frontend but could recompute and verify
    booking_doc = Booking(
        quote_id=b.quote_id,
        name=b.name,
        email=b.email,
        phone=b.phone,
        address=b.address,
        zip_code=b.zip_code,
        lawn_size_sqft=b.lawn_size_sqft,
        frequency=b.frequency,
        extras=b.extras,
        notes=b.notes,
        preferred_date=None if not b.preferred_date else __import__("datetime").date.fromisoformat(b.preferred_date),
        price_total=b.price_total,
        status="confirmed",
    )
    try:
        booking_id = create_document("booking", booking_doc)
        return {"id": booking_id, **booking_doc.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bookings")
def list_bookings(limit: int = 50):
    try:
        docs = get_documents("booking", {}, limit)
        return [serialize_doc(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
