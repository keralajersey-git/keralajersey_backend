from fastapi import FastAPI
from app.routes import products

app = FastAPI(title="Kerala Jersey Backend")

# Include routers
app.include_router(products.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Kerala Jersey API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
