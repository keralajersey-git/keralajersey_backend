from fastapi import APIRouter, HTTPException, Query
from app.services.db_service import DBService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/")
async def get_all_reviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
    search: str = Query(""),
):
    try:
        return DBService.get_all_reviews(
            page=page, limit=limit, search=search.strip()
        )
    except Exception as e:
        import traceback
        print(f"Error in get_all_reviews: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/{review_id}")
async def delete_review(review_id: str):
    try:
        DBService.delete_review(review_id)
        return {"message": "Review deleted successfully"}
    except Exception as e:
        print(f"Error deleting review: {e}")
        raise HTTPException(status_code=400, detail=str(e))