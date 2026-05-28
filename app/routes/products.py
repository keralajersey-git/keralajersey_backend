from fastapi import APIRouter, HTTPException, Request
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.services.db_service import DBService
from app.config import BLOB_STORE_ID, verify_webhook_signature
import json

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=Product, response_model_by_alias=True)
async def create_product(product: ProductCreate):
    try:
        response = DBService.create_product(product)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_products():
    try:
        products = DBService.get_products()
        return products
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}", response_model=Product, response_model_by_alias=True)
async def get_product(product_id: str):
    product = DBService.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=Product, response_model_by_alias=True)
async def update_product(product_id: str, product_update: ProductUpdate):
    try:
        response = DBService.update_product(product_id, product_update)
        if not response:
            raise HTTPException(status_code=404, detail="Product not found")
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(product_id: str):
    try:
        DBService.delete_product(product_id)
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/storage/webhook")
async def storage_webhook(request: Request):
    raw_body = await request.body()
    signature_header = (
        request.headers.get("x-blob-signature")
        or request.headers.get("x-signature")
        or request.headers.get("x-hub-signature")
    )

    if not signature_header:
        raise HTTPException(status_code=400, detail="Missing webhook signature header")

    if not verify_webhook_signature(raw_body, signature_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    store_id = payload.get("store_id")
    if BLOB_STORE_ID and store_id != BLOB_STORE_ID:
        raise HTTPException(status_code=400, detail="Webhook store ID mismatch")

    return {
        "status": "ok",
        "store_id": store_id,
        "event": payload.get("event"),
        "payload": payload,
    }
