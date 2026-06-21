from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import products
from app.config import get_db_connection
import traceback
import os

app = FastAPI(title="Kerala Jersey Backend")

# Configure CORS - MUST be first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://keralajersey.vercel.app",
        "https://keralajersey.in",
        "https://www.keralajersey.in",
    ],
    allow_origin_regex=r"https://(www\.)?keralajersey(-.*)?\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Global exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"Exception on {request.url.path}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        headers={"Access-Control-Allow-Origin": "*"},
        content={"detail": str(exc)},
    )

# Include routers
app.include_router(products.router)


@app.get("/")
async def root():
    return {"message": "Kerala Jersey Backend API is running"}


@app.get("/health")
async def health_check():
    conn = None
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        print(f"Health check - DB error: {e}")
        return {"status": "degraded", "database": "disconnected", "error": str(e)}
