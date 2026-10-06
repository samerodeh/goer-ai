import json
from pathlib import Path

menu_path = Path(__file__).resolve().parent.parent / "data" / "menu.json"

with menu_path.open(encoding="utf-8") as file:
    PRODUCTS = json.load(file)


def search_menu(product_name, merchant_id=None):
    matches = []

    for product in PRODUCTS:
        if merchant_id is not None and product["merchant_id"] != merchant_id:
            continue

        if product_name.lower() in product["name"].lower():
            matches.append(product)

    return matches


SEARCH_MENU_TOOL = {
    "type": "function",
    "function": {
        "name": "search_menu",
        "description": (
            "Search LocalGo menu items by a word or phrase in their name. "
            "Optionally restrict the search to one merchant."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "A product name or keyword, such as sandwich.",
                },
                "merchant_id": {
                    "type": ["string"],
                    "enum": ["al-taib", "chateau-kabab"],
                    "description": (
                        "The merchant to search. Omit to search both merchants."
                    ),
                },
            },
            "required": ["product_name"],
        },
    },
}

# print(len(PRODUCTS))
# print(search_menu("sandwich", merchant_id="al-taib"))
