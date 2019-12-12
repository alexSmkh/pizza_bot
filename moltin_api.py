import os

import requests
from requests.exceptions import HTTPError

from utils import create_product_slug


moltin_api_token = None


def create_access_token():
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_secret': os.getenv('MOLTIN_CLIENT_SECRET'),
        'client_id': os.getenv('MOLTIN_CLIENT_ID'),
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=data)
    response.raise_for_status()

    global moltin_api_token
    moltin_api_token = response.json()["access_token"]


def request_api(type_of_request, **request_args):
    request_methods = {
        'get': requests.get,
        'post': requests.post,
        'delete': requests.delete
    }
    request_method = request_methods[type_of_request]

    if moltin_api_token is None:
        create_access_token()

    try:
        response = request_method(**request_args)
        response.raise_for_status()
        return response
    except HTTPError:
        if response.json()['errors'][0]['status'] == 401:
            create_access_token()
            request_args['headers']['Authorization'] = f'Bearer {moltin_api_token}'
            return request_api(type_of_request, **request_args)


def get_default_header():
    return {'Authorization': f'Bearer {moltin_api_token}'}


def get_products():
    url = 'https://api.moltin.com/v2/products'
    response = request_api('get', url=url, headers=get_default_header())
    return response.json()['data']


def delete_all_products():
    for product in get_products():
        url = f'https://api.moltin.com/v2/products/{product["id"]}'
        headers = get_default_header()
        data = {
            'id': product['id']
        }
        request_api('delete', url=url, headers=headers, json=data)


def delete_all_files():
    url = f'https://api.moltin.com/v2/files'
    headers = get_default_header()
    files = request_api('get', url=url, headers=headers).json()['data']
    for file in files:
        url = f'https://api.moltin.com/v2/files/{file["id"]}'
        data = {'id': file['id']}
        request_api('delete', url=url, headers=headers, json=data)


def get_product(product_id):
    url = f'https://api.moltin.com/v2/products/{product_id}'
    response = request_api('get', url=url, headers=get_default_header())
    return response.json()['data']


def get_product_image_url(image_id):
    url = f'https://api.moltin.com/v2/files/{image_id}'
    response = request_api('get', url=url, headers=get_default_header())
    return response.json()['data']['link']['href']


def add_product_to_cart(product_id, quantity, user_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items'
    headers = get_default_header()
    headers.update({
        'Content-Type': 'application/json',
        'X-MOLTIN-CURRENCY': 'RUB',
    })
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }
    request_api('post', url=url, headers=headers, json=payload)


def get_user_cart_items(user_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items'
    response = request_api('get', url=url, headers=get_default_header())
    return response.json()['data']


def get_user_cart_item_ids(user_id):
    return set(item['product_id'] for item in get_user_cart_items(user_id))


def get_user_cart(user_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}'
    response = request_api('get', url=url, headers=get_default_header())
    return response.json()['data']


def delete_cart(user_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}'
    request_api('delete', url=url, headers=get_default_header())


def delete_product_from_cart(user_id, product_id):
    url = f'https://api.moltin.com/v2/carts/{user_id}/items/{product_id}'
    request_api('delete', url=url, headers=get_default_header())


def create_customer(name, email):
    url = 'https://api.moltin.com/v2/customers'
    headers = get_default_header()
    headers.update({'Content-Type': 'application/json'})
    data = {
        'data': {
            'type': 'customer',
            'name': f'{name}',
            'email': f'{email}'
        }
    }
    request_api('post', url=url, headers=headers, json=data)


def create_address(customer_id, username, address, location, phone_number):
    url = f'https://api.moltin.com/v2/customers/{customer_id}/addresses'
    header = get_default_header()
    first_name, last_name = username.split(' ')
    data = {
        'type': 'json',
        'first_name': first_name,
        'last_name': last_name,
        'phone_number': phone_number,
        'line_1': address,
        'line_2': location,
        'county': 'None',
        'postcode': 'None',
        'country': 'RU'
    }
    request_api('post', url=url, headers=header, json=data)


def get_flow_entries(flow_name, entry_id=None):
    if entry_id is None:
        url = f'https://api.moltin.com/v2/flows/{flow_name}/entries'
    else:
        url = f'https://api.moltin.com/v2/flows/{flow_name}/entries/{entry_id}'
    header = get_default_header()
    data = {
        'slug': flow_name,
    }
    return request_api('get', url=url, headers=header, json=data).json()['data']


def link_main_image_and_product(product_id, image_id):
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = get_default_header()
    headers.update({'Content-Type': 'application/json'})
    data = {
        'data': {
            'type': 'main_image',
            'id': image_id
        }
    }
    request_api('post', url=url, headers=headers, json=data)


def upload_file_to_moltin(filepath):
    url = 'https://api.moltin.com/v2/files'
    headers = get_default_header()
    with open(filepath, 'rb') as file:
        data = {
            'file': file,
            'public': True
        }
        response = request_api('post', url=url, headers=headers, files=data)
    return response.json()


def get_file_by_id(id):
    url = f'https://api.moltin.com/v2/files/{id}'
    headers = get_default_header()
    response = request_api('get', url=url, headers=headers)
    return response.json()['data']


def create_product(product_data):
    url = 'https://api.moltin.com/v2/products'
    headers = get_default_header()
    headers.update({'Content-Type': 'application/json'})
    product_slug = create_product_slug(product_data['name'])
    data = {
        'data': {
            'type': 'product',
            'name': product_data['name'],
            'slug': product_slug,
            'sku': str(product_data['id']),
            'manage_stock': False,
            'description': product_data['description'],
            'price': [
                {
                    'amount': product_data['price'],
                    'currency': 'RUB',
                    'includes_tax': True
                }
            ],
            'commodity_type': 'physical',
            'status': 'live'
        }
    }
    response = request_api('post', url=url, headers=headers, json=data)
    return response.json()


def create_flow(flow_name):
    url = 'https://api.moltin.com/v2/flows'
    headers = get_default_header()
    headers.update({'Content-Type': 'application/json'})
    data = {
        'data': {
            'type': 'flow',
            'name': f'{flow_name}'.capitalize(),
            'slug': f'{flow_name.replace(" ", "_")}',
            'description': f'{flow_name} description ...'.capitalize(),
            'enabled': True
        }
    }
    response = request_api('post', url=url, headers=headers, json=data)
    return response.json()


def create_flow_field(field_data):
    url = 'https://api.moltin.com/v2/fields'
    headers = get_default_header()
    headers.update({'Content-Type': 'application/json'})
    data = {
        'data': {
            'type': 'field',
            'name': field_data['name'],
            'slug': field_data['slug'],
            'field_type': field_data['field_type'],
            'description': field_data['description'],
            'required': bool(field_data['required']),
            'enabled': True,
            'unique': True,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': field_data['flow_id']
                    }
                }
            }

        }
    }
    request_api('post', url=url, headers=headers, json=data)


def create_flow_entry(flow_slug, entry_data):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = get_default_header()
    headers.update({'Content-Type': 'application/json'})
    return request_api(
        'post',
        url=url, headers=headers, json=entry_data).json()['data']


def delete_flow_entry(flow_slug, entry_id):
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries/{entry_id}'
    request_api('delete', url=url, headers=get_default_header())
