import os

CUSTOMER_ADDRESS_SLUG = 'customer_address'

PIZZERIA_FLOW_FIELDS = [
    {
        "name": "Address",
        "slug": "address",
        "field_type": "string",
        "description": "Address",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Alias",
        "slug": "alias",
        "field_type": "string",
        "description": "Alias",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Longitude",
        "slug": "longitude",
        "field_type": "float",
        "description": "Longitude",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Latitude",
        "slug": "latitude",
        "field_type": "float",
        "description": "Latitude",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Courier",
        "slug": "courier",
        "field_type": "integer",
        "description": "Telegram ID of a courier",
        "required": 1,
        "flow_id": ""
    }
]


CUSTOMER_ADDRESS_FLOW_FIELDS = [
    {
        "name": "Customer telegram id",
        "slug": "customer_telegram_id",
        "field_type": "integer",
        "description": "customer telegram id",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Longitude",
        "slug": "longitude",
        "field_type": "float",
        "description": "longitude",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Latitude",
        "slug": "latitude",
        "field_type": "float",
        "description": "latitude",
        "required": 1,
        "flow_id": ""
    },
    {
        "name": "Customer phone number",
        "slug": "customer_phone_number",
        "field_type": "integer",
        "description": "Customer phone number",
        "required": 1,
        "flow_id": ""
    }
]


def get_address_data_for_creating_entry(address):
    return {
        'data': {
            'type': 'entry',
            'alias': address['alias'],
            'address': address['address']['full'],
            'longitude': address['coordinates']['lon'],
            'latitude': address['coordinates']['lat'],
            'courier': int(os.getenv('TEST_TELEGRAM_ID'))
        }
    }


def get_customer_address_for_creating_entry(telegram_id, longitude,
                                            latitude, phone):
    return {
        'data': {
            'type': 'entry',
            'customer_telegram_id': telegram_id,
            'longitude': longitude,
            'latitude': latitude,
            'customer_phone_number': phone
        }
    }

