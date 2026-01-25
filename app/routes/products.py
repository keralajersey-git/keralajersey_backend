from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.services.appwrite_service import AppwriteService
from appwrite.input_file import InputFile
from appwrite.id import ID
from app.config import storage, APPWRITE_BUCKET_ID, APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID
import json

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=Product, response_model_by_alias=True)
async def create_product(product: ProductCreate):
    try:
        response = AppwriteService.create_product(product)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Product], response_model_by_alias=True)
async def get_products():
    try:
        return AppwriteService.get_products()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{product_id}", response_model=Product, response_model_by_alias=True)
async def get_product(product_id: str):
    try:
        return AppwriteService.get_product(product_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Product not found")

@router.put("/{product_id}", response_model=Product, response_model_by_alias=True)
async def update_product(product_id: str, product_update: ProductUpdate):
    try:
        response = AppwriteService.update_product(product_id, product_update)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{product_id}")
async def delete_product(product_id: str):
    try:
        AppwriteService.delete_product(product_id)
        return {"message": "Product deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        input_file = InputFile.from_bytes(file_content, file.filename)
        
        response = storage.create_file(
            bucket_id=APPWRITE_BUCKET_ID,
            file_id=ID.unique(),
            file=input_file
        )
        
        # Construct the view URL
        image_url = f"{APPWRITE_ENDPOINT}/storage/buckets/{APPWRITE_BUCKET_ID}/files/{response['$id']}/view?project={APPWRITE_PROJECT_ID}"
        
        return {
            "file_id": response["$id"],
            "url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
