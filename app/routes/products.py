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
    pinned: bool = Query(False),
):
    try:
        products = DBService.get_products(
            page=page,
            limit=limit,
            search=search.strip(),
            category=category.strip() or None,
            sub_category=sub_category.strip() or None,
            pinned_only=pinned,
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
        import os
        import urllib.parse
        import urllib.request
        import json

        api_key = os.getenv("IMGPILE_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500, detail="IMGPILE_API_KEY is not configured"
            )
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")
        filename = file.filename or "upload.jpg"
        query = urllib.parse.urlencode({"filename": filename})
        req = urllib.request.Request(
            "https://imgpile.com/uploads?" + query,
            data=file_content,
            headers={
                "Authorization": "Bearer " + api_key,
                "Content-Type": "application/octet-stream",
                "User-Agent": "keralajersey-backend/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = resp.status
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            raise HTTPException(
                status_code=502, detail=f"ImgPile upload failed: {str(e)}"
            )
        if status != 201:
            raise HTTPException(
                status_code=502, detail=f"ImgPile upload failed: HTTP {status}"
            )
        try:
            payload = json.loads(body)
        except Exception:
            raise HTTPException(
                status_code=502, detail="ImgPile returned non-JSON response"
            )
        node = payload.get("data") or {}
        urls = node.get("urls") or {}
        original = urls.get("original") or ""
        if not original.startswith("https://"):
            raise HTTPException(
                status_code=502, detail="ImgPile response missing original URL"
            )
        return {"url": original}
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


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
