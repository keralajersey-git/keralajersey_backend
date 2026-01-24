from pydantic import BaseModel, Field, model_validator
from typing import List, Optional

class ProductBase(BaseModel):
    title: str
    description: str
    category: str
    available_sizes: List[str]
    stock: bool = True
    stock_left: Optional[int] = None
    price: float
    free_delivery: bool = False

    @model_validator(mode='after')
    def check_stock_left(self):
        if self.stock and self.stock_left is None:
            raise ValueError('stock_left must be provided if stock is True')
        return self

class ProductCreate(ProductBase):
    # These will be Appwrite file IDs after upload
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
