
from typing import List
from wa.dish import DishType
from pydantic import BaseModel

class OrderType(BaseModel):
    table: int # table: 1
    dishes: List[dict] # {dish: 1, quantity: 1}

# This will be inserted in the queue
class Order:
    def __init__(self, dishes: List[dict]):
        self.dishes = dishes

    def __str__(self) -> str:
        dishes_str = ""
        for dish in self.dishes:
            dish_str = dish["dish"]
            dish_quantity = dish["quantity"]
            dishes_str += f"({dish_str}, {dish_quantity})-"
        return f"(dishes: {dishes_str})"