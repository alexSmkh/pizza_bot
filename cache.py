import time
import json

from moltin_api import get_products_of_category
from redis_db import get_database_connection
from global_variables import PIZZA_CATEGORIES

from dotenv import load_dotenv


database = None


def cache_menu():
    while True:
        menu = {
            category: get_products_of_category(category)
            for category in PIZZA_CATEGORIES.keys()
        }

        global database
        if database is None:
            database = get_database_connection(database)

        database.set('menu', json.dumps(menu))
        time.sleep(300)


def get_menu_from_cache():
    global database
    if database is None:
        database = get_database_connection(database)
    return json.loads(database.get('menu').decode('utf-8'))


if __name__ == '__main__':
    load_dotenv()
    cache_menu()
