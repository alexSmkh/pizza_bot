from moltin_api import get_products, get_file_by_id
from global_variables import (SHOPPING_CART, CHECK_MARK, RUB, SHOPPING_BAGS,
                              CREDIT_CARD, PIZZERIA_LOGO_URL)
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


def get_menu():
    number_of_pizzas_in_carousel = 5
    products = get_products()[:number_of_pizzas_in_carousel]
    menu = get_main_card()
    product_cards = [
        {
            "title": (f"{product['name']} "
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
    return menu
