
class Dish:
    dish = 0
    title = ""
    description = ""
    pieces = 0
    price = 0
    def __init__(self, dish, title, description, pieces, price) -> None:
        self.dish = dish
        self.title = title
        self.description = description
        self.pieces = pieces
        self.price = price