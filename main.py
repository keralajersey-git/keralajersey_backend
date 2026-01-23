from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import products

app = FastAPI(title="Kerala Jersey Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Kerala Jersey API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
