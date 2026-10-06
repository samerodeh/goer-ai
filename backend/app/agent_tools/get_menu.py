from app.agent_tools.menu_data import menu_data

def get_menu(merchant_id:str) -> list[dict]:
    products_result = []
    for product in menu_data: # loop through each dict in the list
        if product["merchant_id"] == merchant_id:

            products_result.append({
                "product_id": product["product_id"],
                "merchant_id": product["merchant_id"],
                "name": product["name"],
                "category": product["category"],
                "price_cents": product["price_cents"],
                "description": product["description"],
            }) # get only the product dict for each matching merchant_id

    return products_result


if __name__ == "__main__":
    print(get_menu("al-taib"))


GET_MENU_TOOL = {
    "type": "function",
    "function": {
        "name": "get_menu",
        "description": (
            "Retrieve all menu items matching the merchant_id "
            "specified by the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "merchant_id": {
                    "type": "string",
                    "enum": ["al-taib", "chateau-kabab"],
                    "description": (
                        "The merchant whose menu should be retrieved."
                    ),
                },
            },
            "required": ["merchant_id"],
        },
    },
}
