from pydantic import BaseModel


class Recommendation(BaseModel):
    name: str
    price: float
    image_url: str
    link: str
    description: str
    rating: float
