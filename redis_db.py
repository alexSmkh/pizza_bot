import redis
import os


def get_database_connection(database):
    if database is None:
        database = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=os.getenv('REDIS_PORT'),
            password=os.getenv('REDIS_PASSWORD')
        )
    return database


def delete_user_data(database, user_id):
    database.delete(f'user_{user_id}:entry_id')
    database.delete(f'user_{user_id}:username')
    database.delete(f'user_{user_id}:phone_number')