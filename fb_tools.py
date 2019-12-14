from cache import get_menu_from_cache
from moltin_api import (get_file_by_id, get_products_of_category,
                        get_all_categories, get_user_cart_item_ids,
                        get_user_cart_items, get_user_cart)
from global_variables import (SHOPPING_CART, CHECK_MARK, RUB, SHOPPING_BAGS,
                              CREDIT_CARD, PIZZERIA_LOGO_URL, LAST_CARD_IMG,
                              PIZZA, PIZZA_CATEGORIES, PLUS, CROSS_MARK,
                              DELIVERY, WALKING, LEFTWARDS_ARROW, CART_LOGO)
from utils import get_short_description_for_fb_menu, \
    get_short_description_for_fb_cart


def get_main_card_for_menu():
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


def get_last_card_for_menu(current_category):
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
    products = get_menu_from_cache()[category]
    menu = get_main_card_for_menu()
    product_cards = [
        {
            "title": (f"{PIZZA} {product['name']} "
                      f"({product['meta']['display_price']['with_tax']['amount']}"
                      f"{RUB})"),
            "image_url": get_file_by_id(
                product['relationships']['main_image']['data']['id']
            )['link']['href'],
            "subtitle": get_short_description_for_fb_menu(product['description']),
            "buttons": [
                {
                    'type': 'postback',
                    'title': f'{CHECK_MARK} Добавить в корзину',
                    'payload': f'add_{product["id"]}'
                },
            ]
        }
        for product in products
    ]
    menu.extend(product_cards)
    menu.append(get_last_card_for_menu(category))
    return menu


def get_main_card_for_cart(cart_id):
    cart = get_user_cart(cart_id)
    total_price = cart['meta']['display_price']['with_tax']['amount']
    return [
        {
            "title": f"{SHOPPING_CART} Корзина",
            "image_url": CART_LOGO,
            "subtitle": f'Ваш заказ на сумму {total_price}{RUB}',
            "buttons": [
                {
                    'type': 'postback',
                    'title': f'{DELIVERY} Доставка',
                    'payload': f'delivery'
                },
                {
                    'type': 'postback',
                    'title': f'{WALKING} Самовывоз',
                    'payload': f'pickup'
                },
                {
                    'type': 'postback',
                    'title': f'{LEFTWARDS_ARROW} К меню',
                    'payload': f'menu'
                },

            ]
        }
    ]


def get_cards_for_cart(cart_id):
    products = get_user_cart_items(cart_id)
    return [
        {
            "title": (f"{PIZZA} {product['name']} "
                      f"({product['unit_price']['amount']}"
                      f"{RUB})"),
            "image_url": product['image']['href'],
            "subtitle": get_short_description_for_fb_cart(product),
            "buttons": [
                {
                    'type': 'postback',
                    'title': f'{CROSS_MARK} Удалить из корзины',
                    'payload': f'remove_{product["id"]}'
                },
                {
                    'type': 'postback',
                    'title': f'{PLUS} Добавить еще',
                    'payload': f'add_{product["id"]}'
                }
            ]
        }
        for product in products
    ]


def get_cart(cart_id):
    cart = []
    main_card = get_main_card_for_cart(cart_id)
    product_cards = get_cards_for_cart(cart_id)

    cart.extend(main_card)
    cart.extend(product_cards)

    return cart
