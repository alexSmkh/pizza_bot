from moltin_api import (get_file_by_id, get_products_of_category,
                        get_all_categories)
from global_variables import (SHOPPING_CART, CHECK_MARK, RUB, SHOPPING_BAGS,
                              CREDIT_CARD, PIZZERIA_LOGO_URL, LAST_CARD_IMG,
                              PIZZA, PIZZA_CATEGORIES)
from utils import get_short_description


def get_main_card():
    return [{
        'title': 'Меню',
        'image_url': PIZZERIA_LOGO_URL,
        'subtitle': 'Выберите один из вариантов',
        'buttons':  [
            {
                'type': 'postback',
                'title': f'{SHOPPING_CART} Корзина',
                'payload': 'cart'
            },
            {
                'type': 'postback',
                'title': f'{SHOPPING_BAGS} Акции',
                'payload': 'sale'
            },
            {
                'type': 'postback',
                'title': f'{CREDIT_CARD} Оформить заказ',
                'payload': 'order'
            },

        ]
    }]


def get_last_card(current_category):
    buttons = []
    for category in get_all_categories():
        if category['name'] == current_category:
            continue
        buttons.append(
            {
                'type': 'postback',
                'title': f'{PIZZA} {PIZZA_CATEGORIES[category["name"]]} {PIZZA}',
                'payload': category['name']
            }
        )

    return {
        'title': 'Не нашли нужную пиццу?',
        'image_url': LAST_CARD_IMG,
        'subtitle': 'Остальные пиццы можно посмотреть в одной из категорий',
        'buttons': buttons
    }


def get_menu(category='Main'):
    products = get_products_of_category(category)
    menu = get_main_card()
    product_cards = [
        {
            "title": (f"{PIZZA} {product['name']} "
                      f"({product['meta']['display_price']['with_tax']['amount']}"
                      f"{RUB})"),
            "image_url": get_file_by_id(
                product['relationships']['main_image']['data']['id']
            )['link']['href'],
            "subtitle": get_short_description(product['description']),
            "buttons": [
                {
                    'type': 'postback',
                    'title': f'{CHECK_MARK} Добавить в корзину',
                    'payload': product['id']
                },
            ]
        }
        for product in products
    ]
    menu.extend(product_cards)
    menu.append(get_last_card(category))
    return menu
