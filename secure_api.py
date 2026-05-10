from fastapi import APIRouter, Depends
from pathlib import Path
import json

from auth_system import get_current_user

secure_router = APIRouter()

@secure_router.get("/api/product-hunter-secure")
async def get_product_hunter_secure(current_user: dict = Depends(get_current_user)):
    final_file = Path("final_products.json")
    supplier_file = Path("supplier_options.json")

    if not final_file.exists():
        return {
            "status": "empty",
            "message": "Run python ultraai_pipeline.py first!",
            "products": [],
            "user": current_user
        }

    products = json.loads(final_file.read_text(encoding="utf-8"))
    suppliers_data = {}

    if supplier_file.exists():
        supplier_list = json.loads(supplier_file.read_text(encoding="utf-8"))
        for s in supplier_list:
            suppliers_data[s.get("product_name_ar")] = s.get("local_suppliers_jo", [])

    for p in products:
        p["local_suppliers"] = suppliers_data.get(p.get("product_name_ar"), [])

    return {
        "status": "success",
        "products": products,
        "user": current_user
    }
