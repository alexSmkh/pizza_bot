import os

from dotenv import load_dotenv

from moltin_api import (create_product, upload_file_to_moltin,
                        link_main_image_and_product, create_flow,
                        create_flow_field, create_flow_entry)
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


def upload_products(menu):
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


if __name__ == '__main__':
    load_dotenv()

    cwd = os.getcwd()
    pizzeria_addresses = read_json_file(
        os.path.join(cwd, 'data_for_load_moltin/pizzeria_addresses.json')
    )
    pizzeria_menu = read_json_file(
        os.path.join(cwd, 'data_for_load_moltin/menu.json')
    )

    upload_products(pizzeria_menu)

    pizzeria_flow = create_flow('pizzeria')

    create_fields(PIZZERIA_FLOW_FIELDS, pizzeria_flow['data']['id'])
    for address in pizzeria_addresses:
        create_flow_entry(
            pizzeria_flow['data']['slug'],
            get_address_data_for_creating_entry(address)
        )

    customer_address_flow = create_flow('customer address')
    create_fields(
        CUSTOMER_ADDRESS_FLOW_FIELDS,
        customer_address_flow['data']['id']
    )
