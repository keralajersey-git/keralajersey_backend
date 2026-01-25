from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "top-quality"
    available_sizes: Optional[List[str]] = ["S", "M", "L", "XL"]
    stock: bool = True
    stock_left: Optional[int] = 0
    price: float = 0.0
    free_delivery: bool = False


class ProductCreate(ProductBase):
    
    image1: str
    image2: Optional[str] = None
    image3: Optional[str] = None

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    available_sizes: Optional[List[str]] = None
    stock: Optional[bool] = None
    stock_left: Optional[int] = None
    price: Optional[float] = None
    free_delivery: Optional[bool] = None
    image1: Optional[str] = None
    image2: Optional[str] = None
    image3: Optional[str] = None

class Product(ProductBase):
    id: str = Field(alias="$id")
    image1: str
    image2: Optional[str] = None
    image3: Optional[str] = None

    class Config:
        populate_by_name = True
