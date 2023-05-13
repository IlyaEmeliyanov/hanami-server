
from pydantic import BaseModel

class DishType(BaseModel):
    _id: dict
    dish: str
    title: str
    description: str
    pieces: int
    price: float
    url: str
    quantity: int

class Dish:
    def __init__(self, dish_str: str, title: str, description: str, pieces: int, price: float, url: str, quantity: int):
        self.dish_str = dish_str
        self.title = title
        self.description = description
        self.pieces = pieces
        self.price = price
        self.url = url
        self.quantity = quantity

    def __str__(self) -> str:
        return f"(dish: {self.dish_str}, title: {self.title}, description: {self.description}, pieces: {self.pieces}, price: {self.price}, url: {self.url}, quantity: {self.quantity})"