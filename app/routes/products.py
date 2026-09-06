from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Query
import os
import json
from io import BytesIO
from app.schemas.product import Product, ProductCreate, ProductUpdate, ReviewCreate
from app.services.db_service import DBService

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=Product, response_model_by_alias=True)
async def create_product(product: ProductCreate):
    try:
        response = DBService.create_product(product)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify backend is working"""
    return {"message": "Backend is working", "status": "ok"}

@router.get("/")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=1000),
    search: str = Query(""),
    category: str = Query(""),
    sub_category: str = Query(""),
):
    try:
        products = DBService.get_products(
            page=page,
            limit=limit,
            search=search.strip(),
            category=category.strip() or None,
            sub_category=sub_category.strip() or None,
        )
        return products
    except Exception as e:
        import traceback
        print(f"Error in get_products: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        import cloudinary
        import cloudinary.uploader
        import os
        
        # Configure cloudinary when endpoint is called
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )
        
        file_content = await file.read()
        
        # Create a BytesIO object for Cloudinary
        file_obj = BytesIO(file_content)
        file_obj.name = file.filename or "upload.png"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_obj,
            folder="keralajersey",
            resource_type="auto",
            public_id=file.filename.split('.')[0] if file.filename else None
        )
        
        return {"url": result.get("secure_url")}
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary SDK not installed: {str(e)}")
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        print(f"Upload error: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {error_msg}")

@router.get("/{product_id}/reviews")
async def get_reviews(product_id: str):
    try:
        reviews = DBService.get_reviews(product_id)
        return reviews
    except Exception as e:
        import traceback
        print(f"Error in get_reviews: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{product_id}/reviews")
async def create_review(product_id: str, review: ReviewCreate):
    try:
        product = DBService.get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        created = DBService.create_review(
            product_id, review.customer_name, review.review
        )
        return created
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in create_review: {e}")
        traceback.print_exc()
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
