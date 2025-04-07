from pydantic import BaseModel, Field
from typing import Optional, List

# Define a Pydantic model for the product data structure
class Product(BaseModel):
    product_name: str = Field(description="The full name of the product")
    price: str = Field(description="Price with currency symbol (e.g., $19.99)")
    url: str = Field(description="Full URL to the product page")
    rating: Optional[str] = Field(None, description="Product rating out of 5 stars (e.g., '4.5 out of 5')")
    reviews: Optional[str] = Field(None, description="Number of customer reviews (e.g., '1,234')")
    seller: Optional[str] = Field(None, description="Name of the seller or brand")

# Define a container model for the list of products
class ProductList(BaseModel):
    products: List[Product] = Field(description="List of products from search results")