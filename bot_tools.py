import math

from moltin_api import (get_products, get_user_cart, get_user_cart_item_ids)

from global_variables import (LOCATION, WRITING, CHECK_MARK, LEFTWARDS_ARROW,
                       CREDIT_CARD, SHOPPING_CART, PIZZA, MINUS, PLUS, OK,
                       CROSS_MARK, DELIVERY, WALKING)
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardMarkup, KeyboardButton

from utils import get_nearest_pizzeria, get_distance_between_points, \
    get_info_about_delivery


def get_add_button(product_id):
    return InlineKeyboardButton(
        f'{CHECK_MARK} Добавить в корзину',
        callback_data=f'add_{product_id}',
    )


def get_payment_button(shipping_price):
    return InlineKeyboardButton(
        f'{CREDIT_CARD} Оплатить',
        callback_data=f'{shipping_price}'
    )


def get_menu_button():
    return InlineKeyboardButton(
        f'{LEFTWARDS_ARROW} В меню',
        callback_data='menu_btn'
    )


def get_ordering_button():
    return InlineKeyboardButton(
        f'{CREDIT_CARD} Оформить заказ',
        callback_data='ordering_btn'
    )


def create_product_buttons(products, page_number, user_id):
    products_on_page = 8
    last_element_index = products_on_page * page_number
    first_element_index = last_element_index - products_on_page
    products_for_current_page = products[first_element_index:last_element_index]
    products_in_cart = get_user_cart_item_ids(user_id)

    button_list = []
    for product in products_for_current_page:
        if product['id'] in products_in_cart:
            text = f'{PIZZA} {product["name"]} ({CHECK_MARK} Уже в корзине)'
        else:
            text = f'{PIZZA} {product["name"]}'

        button_list.append(
            [InlineKeyboardButton(text, callback_data=f'id_{product["id"]}')]
        )
    return button_list


def get_cart_button(user_id):
    user_cart = get_user_cart(user_id)
    total_amount = int(user_cart['meta']['display_price']['with_tax']['amount'])
    if total_amount:
        text_on_button = f'{SHOPPING_CART} Корзина (Итог на сумму: {total_amount}₽)'
    else:
        text_on_button = f'{SHOPPING_CART} Корзина'
    return InlineKeyboardButton(text_on_button, callback_data='cart_')


def create_selection_buttons(quantity_of_pizzas, product_id):
    button_list = [
        [
            InlineKeyboardButton(
                f'{MINUS}',
                callback_data=f'minus_{quantity_of_pizzas}_{product_id}',
            ),
            InlineKeyboardButton(
                f'{quantity_of_pizzas} шт.',
                callback_data='number_of_pizza_btn',
            ),
            InlineKeyboardButton(
                f'{PLUS}',
                callback_data=f'plus_{quantity_of_pizzas}_{product_id}',
            )
        ],
        [InlineKeyboardButton(
            f'{OK}',
            callback_data=f'ok_{quantity_of_pizzas}_{product_id}'
        )],
    ]
    return InlineKeyboardMarkup(button_list)


def create_delivery_selection_buttons(distance_to_pizzeria, user_entry_id):
    if distance_to_pizzeria <= 20:
        keyboard = [
            [InlineKeyboardButton(
                text=f'{DELIVERY} Доставка',
                callback_data=f'delivery_{user_entry_id}'
            )],
            [InlineKeyboardButton(
                text=f'{WALKING} Самовывоз',
                callback_data=f'pickup_{user_entry_id}'
            )]
        ]
    elif distance_to_pizzeria <= 50:
        keyboard = [
            [InlineKeyboardButton(text='Да', callback_data='pickup')],
            [InlineKeyboardButton(
                text='Нет, отказываюсь от заказа',
                callback_data='refusal'
            )]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton(
                'Отменить заказ',
                callback_data='refusal')]
        ]
    return InlineKeyboardMarkup(keyboard)


def get_remove_buttons(user_cart_items):
    remove_buttons = [
        [InlineKeyboardButton(
            f'{CROSS_MARK} Удалить "{item["name"]}"',
            callback_data=f'remove_{item["id"]}'
        )]
        for item in user_cart_items
    ]
    return remove_buttons


def create_pagination(number_of_products, page_number):
    if number_of_products < 9:
        return None

    products_on_page = 8
    number_of_pages = math.ceil(number_of_products / products_on_page)

    if 3 < page_number < number_of_pages - 2:
        first_button = InlineKeyboardButton('↞ 1', callback_data='page_1')
        second_button = InlineKeyboardButton(f'← {page_number - 1}', callback_data=f'page_{page_number - 1}')
        third_button = InlineKeyboardButton(f'⋅{page_number}⋅', callback_data=f'page_{page_number}')
        fourth_button = InlineKeyboardButton(f'{page_number + 1} →', callback_data=f'page_{page_number + 1}')
        fifth_button = InlineKeyboardButton(f'{number_of_pages} ↠', callback_data=f'page_{number_of_pages}')
        button_list = [
            first_button, second_button, third_button, fourth_button,
            fifth_button
        ]
        return button_list

    products_for_five_pages = 35
    if number_of_products < (products_for_five_pages + 1):
        button_list = [
            InlineKeyboardButton(f'⋅{number}⋅', callback_data=f'page_{number}')
            if page_number == number
            else InlineKeyboardButton(f'{number}',
                                      callback_data=f'page_{number}')
            for number in range(1, number_of_pages)
        ]
        return button_list

    first_three_pages = 3
    number_of_first_button = 1
    number_of_fourth_button = 4
    if page_number <= first_three_pages:
        button_list = [
            InlineKeyboardButton(f'⋅{number}⋅', callback_data=f'page_{number}')
            if page_number == number
            else InlineKeyboardButton(f'{number}', callback_data=f'page_{number}')
            for number in range(number_of_first_button, number_of_fourth_button)
        ]
        button_list.append(InlineKeyboardButton('4 →', callback_data='page_4'))
        button_list.append(
            InlineKeyboardButton(
                f'{number_of_pages} ↠',
                callback_data=f'page_{number_of_pages}'
            )
        )
        return button_list

    number_of_fifth_button = number_of_pages
    number_of_third_button = number_of_pages - 2
    if page_number >= number_of_pages - 2:
        button_list = [
            InlineKeyboardButton('↞ 1', callback_data='page_1'),
            InlineKeyboardButton(
                f'← {number_of_pages - 3}',
                callback_data=f'page_{number_of_pages - 3}',
            )
        ]
        for number in range(number_of_third_button, number_of_fifth_button + 1):
            if page_number == number:
                button_list.append(
                    InlineKeyboardButton(
                        f'⋅{number}⋅',
                        callback_data=f'page_{number}'
                    )
                )
            else:
                button_list.append(
                    InlineKeyboardButton(
                        f'{number}',
                        callback_data=f'page_{number}')
                )
        return button_list


def create_menu(user_id, page_number=1):
    all_products = get_products()
    menu = create_product_buttons(all_products, page_number, user_id)
    pagination = create_pagination(len(all_products), page_number)
    if pagination is not None:
        menu.append(pagination)
    menu.append([get_cart_button(user_id)])
    return InlineKeyboardMarkup(menu)


def get_keyboard_for_location_request():
    keyboard = [
        [KeyboardButton(f'{LOCATION} Отправить локацию', request_location=True)],
        [KeyboardButton(f'{WRITING} Напишу адрес')]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True,)


def create_keyboard_for_confirm():
    keyboard = [
            [InlineKeyboardButton('Всё верно', callback_data='yes')],
            [InlineKeyboardButton('Данные некорректны', callback_data='no')],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_keyboard_for_cart(user_cart_items):
    button_list = [
        *get_remove_buttons(user_cart_items),
        [get_menu_button()],
        [get_ordering_button()],
    ]
    return InlineKeyboardMarkup(button_list)


def create_keyboard_for_product_description(user_id, product_id):
    button_list = [
        [get_add_button(product_id)],
        [get_cart_button(user_id)],
        [get_menu_button()],
    ]
    return InlineKeyboardMarkup(button_list)


def get_ui_elements_for_delivery_handler(user_entry_id, user_location, pizzerias):
    nearest_pizzeria = get_nearest_pizzeria(user_location, pizzerias)
    distance_to_pizzeria = get_distance_between_points(
        user_location,
        (nearest_pizzeria['latitude'], nearest_pizzeria['longitude']),
    )

    if distance_to_pizzeria <= 50:
        pizzeria_location = (
            nearest_pizzeria['latitude'],
            nearest_pizzeria['longitude']
        )
    else:
        pizzeria_location = False

    delivery_info = get_info_about_delivery(
        nearest_pizzeria,
        distance_to_pizzeria
    )
    delivery_selection_buttons = create_delivery_selection_buttons(
        distance_to_pizzeria,
        user_entry_id
    )
    return delivery_info, delivery_selection_buttons, pizzeria_location


