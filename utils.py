import argparse
import json
import os
import re

import phonenumbers
from geopy.distance import distance
import requests
import cyrtranslit

import global_variables
from global_variables import DELIVERY, PIZZA, MONEY_BAG, RUB, LIST


def set_flag_for_using_cache():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', action='store_true', help='arg for using cache or not')
    args = parser.parse_args()
    global_variables.use_cache = args.cache


def get_product_info(product_data):
    name = f'\"{product_data["name"]}\"'
    description = f'{LIST} {product_data["description"]}'
    price = f'{product_data["price"][0]["amount"]}'
    return f'{PIZZA} *{name}*\n\n{description}\n*Цена: {price}*{RUB}'


def get_short_description_for_fb_menu(description):
    short_description = description.split('\n')[0]
    return short_description.strip('Состав: ')


def get_short_description_for_fb_cart(product_info):
    return (f'В корзине: {product_info["quantity"]}шт. '
            f'На сумму: {product_info["value"]["amount"]}{RUB}')


def get_cart_info(user_cart_items):
    cart_info = str()
    total_price = 0
    for item in user_cart_items:
        cart_info += f'{PIZZA} \"{item["name"]}\" --- {item["quantity"]} шт. на сумму {item["value"]["amount"]}{RUB}\n'
        total_price += item["value"]["amount"]
    cart_info += f'{MONEY_BAG} Итог: {total_price}{RUB}'
    return cart_info


def get_order_info_for_invoice(user_cart_items, order_price, shipping_price):
    order_info = str()
    price = order_price + shipping_price
    for item in user_cart_items:
        order_info += f'{PIZZA} \"{item["name"]}\" --- {item["quantity"]} шт. на сумму {item["value"]["amount"]}{RUB}\n'
    order_info += f'{DELIVERY} Доставка: {shipping_price}{RUB}\n'
    order_info += f'{MONEY_BAG} Итог: {price}{RUB}'
    return order_info


def get_order_info_for_courier(user_cart_items, username, phone_number):
    order_info = f'Заказ:\n'
    for item in user_cart_items:
        order_info += f'{PIZZA} \"{item["name"]}\" --- {item["quantity"]} шт.\n'
    order_info += ('\nДанные клиента\n'
                   f'Имя: {username}\n'
                   f'Номер телефона: {phone_number}')
    return order_info


def read_json_file(file_path):
    with open(file_path, 'r') as file_handler:
        file = json.load(file_handler)
    return file


def init_data_of_pizzerias():
    pizzeria_addresses = read_json_file(
        os.path.join(
            os.getcwd(),
            'data_for_load_moltin/address.json'
        )
    )
    pizzeria_menu = read_json_file(
        os.path.join(
            os.getcwd(),
            'data_for_load_moltin/menu.json'
        )
    )
    return pizzeria_addresses, pizzeria_menu


def get_pizza_description(pizza_data):
    composition = f'Состав: {pizza_data["description"]}'
    weight = f'Масса: {pizza_data["food_value"]["weight"]}г'
    food_values = f'Пищевая ценность на 100г:'
    carbohydrates = f'Углеводы: {pizza_data["food_value"]["carbohydrates"]}г'
    fats = f'Жиры: {pizza_data["food_value"]["fats"]}г'
    proteins = f'Белки: {pizza_data["food_value"]["proteins"]}г'
    kilocalories = f'Калорийность: {pizza_data["food_value"]["kiloCalories"]}ккал'
    description = f'{composition}\n{weight}\n{food_values}\n{carbohydrates}\n{fats}\n{proteins}\n{kilocalories}\n'
    return description


def write_file(filename, content):
    with open(f'{filename}', 'wb') as file:
        file.write(content)


def download_file(file_url):
    response = requests.get(file_url)
    response.raise_for_status()

    filename = file_url.split('/')[-1]
    write_file(filename, response.content)

    return os.path.join(os.getcwd(), filename)


def create_product_slug(product_name):
    transliteration = cyrtranslit.to_latin(product_name, 'ru')
    replacing_quotes = re.sub("'", '', transliteration)
    return re.sub(' +', '_', replacing_quotes)


def is_phone_number_valid(phone_number):
    try:
        parse = phonenumbers.parse(phone_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False
    if phonenumbers.is_valid_number_for_region(parse, 'RU'):
        return parse.national_number


def get_geodata(location):
    url = 'https://geocode-maps.yandex.ru/1.x'
    params = {
        'geocode': location,
        'apikey': os.getenv('GEOCODER_KEY'),
        'format': 'json',
        'sco': 'latlong',
    }
    response = requests.get(url, params=params)

    if not response.ok:
        return None

    result = response.json()['response']['GeoObjectCollection']\
        ['metaDataProperty']['GeocoderResponseMetaData']['found']
    if not int(result):
        return None
    geo_object = response.json()['response']['GeoObjectCollection']\
        ['featureMember'][0]['GeoObject']

    address = geo_object['metaDataProperty']['GeocoderMetaData']\
        ['Address']['formatted']
    longitude, latitude = map(float, geo_object['Point']['pos'].split(' '))
    full_address = {
        'address': address,
        'latitude': latitude,
        'longitude': longitude
    }
    return full_address


def get_nearest_pizzeria(user_location, pizzerias):
    return min(
        pizzerias,
        key=lambda pizzeria: distance(
            user_location,
            (pizzeria['latitude'], pizzeria['longitude'])
        )
    )


def get_distance_between_points(first_point, second_point):
    return distance(first_point, second_point).km


def get_info_about_delivery(pizzeria, distance):
    if distance <= 0.5:
        metres = round(distance * 1000)
        return (f'Вы находитесь в {metres}м от пиццерии.\n'
                f'Вот её адрес: {pizzeria["address"]}.\n'
                f'Предлагаем забрать заказ самостоятельно, '
                'либо мы доставим бесплатно.')
    elif distance <= 5:
        return 'Доставка будет стоить 100 рублей.\nДоставляем или самовывоз?'
    elif distance <= 20:
        return 'Доставка будет стоить 300 рублей.\nДоставляем или самовывоз?'
    elif distance <= 50:
        return (f'Ближайшая пиццерия в {int(distance)}км от Вас. ' 
                f'К сожалению, мы не доставляем так далеко. Предлагаем самовывоз.\n' 
                'Заберете заказ самостоятельно?')
    else:
        return ('Простите, но так далеко мы пиццу не доставим.\n' 
                f'Ближайшая пиццерия аж в {int(distance)}км от Вас!')


def get_shipping_price(distance):
    if distance <= 0.5:
        return 0
    elif distance <= 5:
        return 100
    elif distance <= 20:
        return 300
