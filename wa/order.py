
class Order:
    def __init__(self, table: str, dishes: list):
        self.table = table
        self.dishes = dishes

    def __str__(self) -> str:
        dishes_str = ""
        for dish in self.dishes:
            dish_str = dish["dish"]
            dish_qty = dish["qty"]
            dishes_str += f"({dish_str}, {dish_qty})-"
        return f"(table: {self.table}, dishes: {dishes_str})"