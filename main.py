from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import products
import traceback

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
    allow_origin_regex=r"https://(www\.)?keralajersey(-.*)?\.vercel\.app",  # Allow Vercel preview deployments
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
        content={"detail": str(exc)},
    )

# Include routers
app.include_router(products.router)


@app.get("/")
async def root():
    return {"message": "Kerala Jersey Backend API is running"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
