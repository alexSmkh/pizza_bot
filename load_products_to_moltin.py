import os

from dotenv import load_dotenv

from moltin_api import (create_product, upload_file_to_moltin,
                        link_main_image_and_product, create_flow,
                        create_flow_field, create_flow_entry, create_category,
                        link_category_and_product)
from utils import read_json_file, get_pizza_description, download_file
from data_for_load_moltin.data_for_flow_fields import (
    PIZZERIA_FLOW_FIELDS,
    CUSTOMER_ADDRESS_FLOW_FIELDS, get_address_data_for_creating_entry)


def create_fields(flow_fields, flow_id):
    for field in flow_fields:
        field['flow_id'] = flow_id
        create_flow_field(field)


def upload_product_image(image_url):
    filepath = download_file(image_url)
    image_creation_response = upload_file_to_moltin(filepath)
    os.remove(filepath)
    return image_creation_response


def create_categories_on_moltin(categories_with_products):
    return {
        category_title: create_category(category_title)['id']
        for category_title, _ in categories_with_products.items()
    }


def get_category_for_product(product_title, categories_with_products):
    for category_title, products in categories_with_products.items():
        print(f'product_title --- {product_title} ===== {products}')
        if product_title in products:
            return category_title


def upload_products(menu, categories_with_ids, categories_with_products):
    for product in menu:
        product['description'] = get_pizza_description(product)
        product_creation_response = create_product(product)
        image_creation_response = upload_product_image(
            product['product_image']['url']
        )

        link_main_image_and_product(
            product_creation_response['data']['id'],
            image_creation_response['data']['id']
        )

        category_id = categories_with_ids[
            get_category_for_product(
                product_creation_response['data']['name'],
                categories_with_products
            )
        ]
        link_category_and_product(
            product_creation_response['data']['id'],
            category_id
        )


if __name__ == '__main__':
    load_dotenv()

    cwd = os.getcwd()
    pizzeria_addresses = read_json_file(
        os.path.join(cwd, 'data_for_load_moltin/pizzeria_addresses.json')
    )
    pizzeria_menu = read_json_file(
        os.path.join(cwd, 'data_for_load_moltin/menu.json')
    )
    pizza_categories_with_pizzas = read_json_file(
        os.path.join(cwd, 'data_for_load_moltin/pizza_categories.json')
    )

    categories_with_ids = create_categories_on_moltin(
        pizza_categories_with_pizzas
    )

    upload_products(
        pizzeria_menu,
        categories_with_ids,
        pizza_categories_with_pizzas
    )
