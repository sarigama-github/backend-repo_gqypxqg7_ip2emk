import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import MenuItem

app = FastAPI(title="McDonald's API", description="API for McDonald's menu and content")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "McDonald's API is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Welcome to McDonald's API"}

# Public menu endpoints

@app.get("/api/menu", response_model=List[MenuItem])
def list_menu(category: Optional[str] = None, featured: Optional[bool] = None, limit: int = 100):
    """List menu items with optional filters"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_dict = {}
    if category:
        filter_dict["category"] = category
    if featured is not None:
        filter_dict["is_featured"] = featured

    items = get_documents("menuitem", filter_dict, limit)

    # Convert Mongo docs to Pydantic-compatible dicts
    result = []
    for doc in items:
        doc.pop("_id", None)
        result.append(MenuItem(**doc))
    return result

class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    image: Optional[str] = None
    is_featured: bool = False
    calories: Optional[int] = None
    spicy_level: Optional[int] = None

@app.post("/api/menu", status_code=201)
def create_menu_item(item: MenuItemCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    try:
        new_id = create_document("menuitem", item.dict())
        return {"id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/menu/seed")
def seed_menu():
    """Seed the database with a few sample McDonald's-style menu items if empty"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["menuitem"].count_documents({})
    if existing > 0:
        return {"status": "exists", "count": existing}

    samples = [
        {
            "name": "Big Mac",
            "description": "Two 100% beef patties, special sauce, lettuce, cheese, pickles, onions on a sesame seed bun.",
            "price": 5.99,
            "category": "Burgers",
            "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=1200",
            "is_featured": True,
            "calories": 550,
            "spicy_level": 0
        },
        {
            "name": "McChicken",
            "description": "Crispy chicken topped with shredded lettuce and mayonnaise on a toasted bun.",
            "price": 3.49,
            "category": "Chicken",
            "image": "https://images.unsplash.com/photo-1561758033-d89a9ad46330?w=1200",
            "is_featured": False,
            "calories": 400,
            "spicy_level": 0
        },
        {
            "name": "World-Famous Fries",
            "description": "Golden, crispy and perfectly salted fries.",
            "price": 2.29,
            "category": "Sides",
            "image": "https://images.unsplash.com/photo-1550547660-31633d40d0a0?w=1200",
            "is_featured": True,
            "calories": 230,
            "spicy_level": 0
        },
        {
            "name": "Spicy McNuggets (10 pc)",
            "description": "Tender, juicy chicken with a spicy tempura coating.",
            "price": 4.99,
            "category": "Chicken",
            "image": "https://images.unsplash.com/photo-1608039829579-8790f8d5a1f7?w=1200",
            "is_featured": True,
            "calories": 420,
            "spicy_level": 3
        },
        {
            "name": "McFlurry Oreo",
            "description": "Vanilla soft serve blended with Oreo cookie pieces.",
            "price": 2.99,
            "category": "Desserts",
            "image": "https://images.unsplash.com/photo-1461009683693-342af2f2d6ce?w=1200",
            "is_featured": False,
            "calories": 510,
            "spicy_level": 0
        },
        {
            "name": "Caramel Iced Coffee",
            "description": "Premium roast coffee over ice with caramel flavor and cream.",
            "price": 2.49,
            "category": "Drinks",
            "image": "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=1200",
            "is_featured": False,
            "calories": 180,
            "spicy_level": 0
        }
    ]

    for s in samples:
        create_document("menuitem", s)

    return {"status": "seeded", "count": len(samples)}

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

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
