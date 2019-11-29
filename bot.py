import os
import logging

from bot_tools import (create_menu, create_keyboard_for_product_description,
                       create_selection_buttons, create_keyboard_for_cart,
                       create_keyboard_for_confirm,
                       get_ui_elements_for_delivery_handler,
                       get_payment_button, get_keyboard_for_location_request)
from data_for_load_moltin.data_for_flow_fields import \
    get_customer_address_for_creating_entry, CUSTOMER_ADDRESS_SLUG
from moltin_api import (get_product_image_url, get_product, add_product_to_cart,
                        delete_product_from_cart, get_user_cart_items,
                        get_flow_entries,
                        create_flow_entry, get_user_cart, delete_cart,
                        delete_flow_entry)
from utils import (get_product_info, get_cart_info, is_phone_number_valid,
                   get_geodata, get_nearest_pizzeria,
                   get_distance_between_points, get_shipping_price,
                   get_order_info_for_courier,
                   get_order_info_for_invoice)
from custom_logger import LogsHandler
from global_variables import WRITING

from dotenv import load_dotenv
from telegram.ext import (Updater, CallbackQueryHandler, MessageHandler, Filters,
                          PreCheckoutQueryHandler, CommandHandler)
from telegram import ParseMode, InlineKeyboardMarkup, LabeledPrice
from redis_db import get_database_connection, delete_user_data

logger = logging.getLogger('Telegram logger')
database = None


def delete_last_message(bot, update):
    bot.delete_message(
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id
    )


def handle_menu(bot, update):
    if update.message:
        user_id = update.message.chat_id
        bot.send_message(
            text='Выберите пиццу:',
            chat_id=user_id,
            reply_markup=create_menu(user_id)
        )
        return 'MENU'

    type_of_callback, callback_value = update.callback_query.data.split('_')
    if type_of_callback == 'start':
        user_id = update.callback_query.message.chat_id
        bot.send_message(
            text='Выберите пиццу:',
            chat_id=user_id,
            reply_markup=create_menu(user_id)
        )
        return 'MENU'
    elif type_of_callback == 'page':
        user_id = update.callback_query.message.chat_id
        bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=create_menu(user_id, int(callback_value))
        )
        return 'MENU'
    elif type_of_callback == 'id':
        delete_last_message(bot, update)
        user_id = update.callback_query.message.chat_id
        product = get_product(callback_value)
        product_image_id = product['relationships']['main_image']['data']['id']
        bot.send_photo(
            chat_id=user_id,
            photo=get_product_image_url(product_image_id),
            caption=get_product_info(product),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_keyboard_for_product_description(
                user_id,
                product_id=callback_value
            ),
        )
        return 'DESCRIPTION'
    elif type_of_callback == 'cart':
        user_id = update.callback_query.message.chat_id
        user_cart_items = get_user_cart_items(user_id)
        cart_info = get_cart_info(user_cart_items)
        delete_last_message(bot, update)
        bot.send_message(
            text=cart_info,
            chat_id=user_id,
            reply_markup=create_keyboard_for_cart(user_cart_items)
        )
        return 'CART'


def handle_description(bot, update):
    type_of_callback, callback_value = update.callback_query.data.split('_')
    user_id = update.callback_query.message.chat_id
    if type_of_callback == 'menu':
        delete_last_message(bot, update)
        bot.send_message(
            text='Выберите пиццу:',
            chat_id=user_id,
            reply_markup=create_menu(user_id)
        )
        return 'MENU'
    elif type_of_callback == 'cart':
        user_cart_items = get_user_cart_items(user_id)
        cart_info = get_cart_info(user_cart_items)
        delete_last_message(bot, update)
        bot.send_message(
            text=cart_info,
            chat_id=user_id,
            reply_markup=create_keyboard_for_cart(user_cart_items)
        )
        return 'CART'
    elif type_of_callback == 'add':
        number_of_pizza = 1
        delete_last_message(bot, update)
        bot.send_message(
            text='Выберите количество',
            chat_id=user_id,
            reply_markup=create_selection_buttons(
                number_of_pizza,
                product_id=callback_value
            )
        )
        return 'SELECTION_QUANTITY_OF_PIZZAS'


def selection_quantity_of_pizzas(bot, update):
    data = update.callback_query.data.split('_')
    type_of_query = data[0]
    quantity_of_pizza = int(data[1])
    product_id = data[2]
    user_id = update.callback_query.message.chat_id
    if type_of_query == 'minus':
        if quantity_of_pizza <= 1:
            return 'SELECTION_QUANTITY_OF_PIZZAS'
        quantity_of_pizza -= 1
        bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=create_selection_buttons(quantity_of_pizza, product_id)
        )
        return 'SELECTION_QUANTITY_OF_PIZZAS'
    elif type_of_query == 'plus':
        quantity_of_pizza += 1
        bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=create_selection_buttons(quantity_of_pizza, product_id)
        )
        return 'SELECTION_QUANTITY_OF_PIZZAS'
    elif type_of_query == 'ok':
        if quantity_of_pizza > 0:
            add_product_to_cart(product_id, quantity_of_pizza, user_id)
        bot.answer_callback_query(
            update.callback_query.id,
            text='Пицца добавлена в корзину',
            show_alert=False
        )
        update.callback_query.data = f'id_{product_id}'
        return handle_menu(bot, update)


def handle_cart(bot, update):
    query, callback_value = update.callback_query.data.split('_')
    user_id = update.callback_query.message.chat_id
    if query == 'remove':
        delete_product_from_cart(
            user_id,
            product_id=callback_value
        )
        user_cart_items = get_user_cart_items(user_id)
        cart_info = get_cart_info(user_cart_items)
        bot.edit_message_text(
            chat_id=user_id,
            message_id=update.callback_query.message.message_id,
            text=cart_info,
            reply_markup=create_keyboard_for_cart(user_cart_items)
        )
        bot.answer_callback_query(
            update.callback_query.id,
            text='Пицца удалена из корзины',
            show_alert=False
        )
        return 'CART'
    elif query == 'menu':
        delete_last_message(bot, update)
        bot.send_message(
            text='Выберите пиццу:',
            chat_id=user_id,
            reply_markup=create_menu(user_id)
        )
        return 'MENU'
    elif query == 'ordering':
        delete_last_message(bot, update)
        bot.send_message(
            chat_id=user_id,
            text='Напишите, пожалуйста, своё имя.'
        )
        return 'WAITING_USERNAME'


def handle_waiting_username(bot, update):
    if update.message:
        username = update.message.text
        database.set(f'user_{update.message.chat_id}:name', username)
        update.message.reply_text('Напишите Ваш номер телефона.')
    return 'WAITING_PHONE_NUMBER'


def handle_waiting_phone_number(bot, update):
    phone_number = update.message.text
    clear_phone_number = is_phone_number_valid(phone_number)
    if not clear_phone_number:
        update.message.reply_text(
            text=(f'Вы неверно ввели номер телефона: {phone_number}.\n' 
                  'Ваш номер телефона должен соответствовать шаблону: +7 *** *** ** **\n' 
                  'Попробуйте еще раз.')
        )
        return 'WAITING_PHONE_NUMBER'
    database.set(
        f'user_{update.message.chat_id}:phone_number',
        clear_phone_number
    )
    username = database.get(
        f'user_{update.message.chat_id}:name'
    ).decode('utf-8')
    bot.send_message(
        chat_id=update.message.chat_id,
        text=(f'Проверьте введенные Вами данные.\n'
              f'Ваше имя: {username}\n' 
              f'Ваш номер телефона: {phone_number}'),
        reply_markup=create_keyboard_for_confirm()
    )
    return 'HANDLE_CONFIRM_PERSONAL_DATA'


def handle_confirm_personal_data(bot, update):
    if update.callback_query.data == 'yes':
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text=('Нам нужно знать Ваше местоположение для доставки. '
                  'Или подсказать ближайшую пиццерию, ' 
                  'если Вы хотите забрать свой заказ сами.\n'
                  'Разрешаете использовать Ваши геоданные?'),
            reply_markup=get_keyboard_for_location_request()
        )
        return 'WAITING_LOCATION'
    else:
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Введите данные еще раз.',
        )


def handle_waiting_user_location(bot, update):
    phone_number = database.get(
        f'user_{update.message.chat_id}:phone_number'
    ).decode('utf-8')
    if update.message:
        if update.message.location:
            longitude = update.message.location.longitude
            latitude = update.message.location.latitude
            current_position = f'{latitude} {longitude}'
        elif update.message.text == f'{WRITING} Напишу адрес':
            return 'WAITING_LOCATION'
        else:
            current_position = update.message.text

        full_address = get_geodata(current_position)
        if not full_address:
            bot.send_message(
                chat_id=update.message.chat_id,
                text=(
                    'Вы, вероятно, ошиблись при вводе адреса. '
                    'Напишите, пожалуйста, еще раз.'
                )
            )
            return 'WAITING_LOCATION'

        customer_address_data = get_customer_address_for_creating_entry(
            update.message.chat_id,
            full_address['longitude'],
            full_address['latitude'],
            phone_number
        )
        user_entry_id = create_flow_entry(
            CUSTOMER_ADDRESS_SLUG,
            customer_address_data
        )['id']
        database.set(f'user_{update.message.chat_id}:entry_id', user_entry_id)

        pizzerias = get_flow_entries('pizzeria')
        user_location = (full_address['latitude'], full_address['longitude'])
        delivery_info, delivery_selection_buttons = \
            get_ui_elements_for_delivery_handler(
                user_entry_id,
                user_location,
                pizzerias
            )
        bot.send_message(
            chat_id=update.message.chat_id,
            text=delivery_info,
            reply_markup=delivery_selection_buttons
        )
        return 'WAITING_FOR_DELIVERY_SELECTION'
    elif update.callback_query:
        bot.send_message(
            chat_id=update.callback_query.message.chat_id,
            text='Напишите ваш адрес.'
        )
        return 'WAITING_LOCATION'


def handle_delivery_selection(bot, update):
    chat_id = update.callback_query.message.chat_id

    if update.callback_query.data == 'refusal':
        bot.send_message(
            chat_id=chat_id,
            text='Жаль, что Вы так далеко.'
        )
        delete_cart(chat_id)
        delete_flow_entry(
            CUSTOMER_ADDRESS_SLUG,
            database.get(f'user_{chat_id}:entry_id').decode('utf-8')
        )
        delete_user_data(database, chat_id)
        update.callback_query.data = 'start_'
        return handle_menu(bot, update)

    query, user_entry_id = update.callback_query.data.split('_')
    user_entry = get_flow_entries(CUSTOMER_ADDRESS_SLUG, user_entry_id)
    user_latitude = user_entry['latitude']
    user_longitude = user_entry['longitude']
    nearest_pizzeria = get_nearest_pizzeria(
        (user_latitude, user_longitude),
        get_flow_entries('pizzeria')
    )
    distance_to_pizzeria = get_distance_between_points(
        (user_latitude, user_longitude),
        (nearest_pizzeria['latitude'], nearest_pizzeria['longitude'])
    )
    if query == 'delivery':
        shipping_price = get_shipping_price(distance_to_pizzeria)
        bot.send_message(
            chat_id=chat_id,
            text=('Мы уже начали собирать Ваш заказ!\n'
                  'После оплаты наш курьер доставит его в пределах 1ч.'),
            reply_markup=InlineKeyboardMarkup(
                [[get_payment_button(shipping_price)]]
            )
        )
        return 'PAYMENT'
    elif query == 'pickup':
        bot.send_message(
            chat_id=chat_id,
            text=('Забрать заказ можно по адресу:\n'
                  f'{nearest_pizzeria["address"]}.')
        )
        bot.send_location(
            chat_id=chat_id,
            latitude=nearest_pizzeria['latitude'],
            longitude=nearest_pizzeria['longitude'],
        )
        shipping_price = 0
        bot.send_message(
            chat_id=chat_id,
            text='Осталось оплатить заказ.',
            reply_markup=InlineKeyboardMarkup(
                [[get_payment_button(shipping_price)]]
            )
        )
        return 'PAYMENT'


def handle_payment(bot, update):
    user_id = update.callback_query.message.chat_id
    shipping_price = int(update.callback_query.data)
    order_price = get_user_cart(user_id)['meta']['display_price']['with_tax']['amount']
    order_info = get_order_info_for_invoice(
        get_user_cart_items(user_id),
        order_price,
        shipping_price,
    )

    bot.sendInvoice(
        chat_id=user_id,
        title='Тестовый платеж',
        description=order_info,
        payload='Custom-Payload',
        provider_token=os.getenv('PROVIDER_TOKEN'),
        start_parameter='test-payment',
        currency='rub',
        prices=[
            LabeledPrice(label='Pizza', amount=order_price*100),
            LabeledPrice(label='Shipping', amount=shipping_price*100)
        ]
    )
    return 'MENU'


def handle_pre_checkout(bot, update):
    query = update.pre_checkout_query
    if query.invoice_payload != 'Custom-Payload':
        bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=False,
            error_message='Что-то пошло не так...'
        )
    else:
        chat_id = query.from_user.id
        bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)
        bot.send_message(chat_id=chat_id, text='Спасибо за покупку!')
        # send_message_to_courier(bot, query.from_user.id)
        delete_user_data(database, query.from_user.id)


def send_message_to_courier(bot, user_id):
    user_cart_items = get_user_cart_items(user_id)
    username = database.get(f'user_{user_id}:name').decode('utf-8')
    user_phone_number = database.get(
        f'user_{user_id}:phone_number'
    ).decode('utf-8')
    order_info = get_order_info_for_courier(
        user_cart_items,
        username,
        user_phone_number
    )

    user_entry_id = database.get(f'user_{user_id}:entry_id').decode('utf-8')
    user_entry = get_flow_entries(CUSTOMER_ADDRESS_SLUG, user_entry_id)
    user_latitude = user_entry['latitude']
    user_longitude = user_entry['longitude']

    nearest_pizzeria = get_nearest_pizzeria(
        (user_latitude, user_longitude),
        get_flow_entries('pizzeria')
    )
    courier_id = nearest_pizzeria['courier']

    bot.send_location(
        chat_id=courier_id,
        latitude=user_latitude,
        longitude=user_longitude
    )
    bot.send_message(
        chat_id=courier_id,
        text=order_info
    )


def create_job_queue(bot, update, job_queue):
    one_hour = 3600
    job_queue.run_once(send_alert, one_hour, context=update.message.chat_id)


def send_alert(bot, job):
    bot.send_message(
        chat_id=job.context,
        text=('Приятного аппетита!\n\n'
              '*место для рекламы*\n'
              '*что делать, если пицца не пришла*')
    )


def handle_users_reply(bot, update):
    global database
    database = get_database_connection(database)

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        database.set(f'user_{chat_id}:state', 'MENU')
        user_state = 'MENU'
    else:
        user_state = database.get(f'user_{chat_id}:state').decode('utf-8')

    states = {
        'MENU': handle_menu,
        'DESCRIPTION': handle_description,
        'CART': handle_cart,
        'SELECTION_QUANTITY_OF_PIZZAS': selection_quantity_of_pizzas,
        'WAITING_USERNAME': handle_waiting_username,
        'WAITING_PHONE_NUMBER': handle_waiting_phone_number,
        'HANDLE_CONFIRM_PERSONAL_DATA': handle_confirm_personal_data,
        'WAITING_LOCATION': handle_waiting_user_location,
        'WAITING_FOR_DELIVERY_SELECTION': handle_delivery_selection,
        'PAYMENT': handle_payment,
        'PRE_CHECKOUT': handle_pre_checkout,
    }
    state_handler = states[user_state]
    try:
        next_state = state_handler(bot, update)
        database.set(f'user_{chat_id}:state', next_state)
    except Exception as err:
        logger.exception(f'Ошибка: {err}')


def run_bot():
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    logger.addHandler(LogsHandler())
    updater = Updater(os.getenv('TELEGRAM_TOKEN'))
    dispather = updater.dispatcher
    dispather.add_handler(CommandHandler('start', handle_users_reply))
    dispather.add_handler(CallbackQueryHandler(handle_users_reply))
    dispather.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispather.add_handler(CommandHandler('start', handle_users_reply))
    dispather.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))
    dispather.add_handler(
        MessageHandler(
            Filters.successful_payment,
            create_job_queue,
            pass_job_queue=True
        )
    )
    dispather.add_handler(
        MessageHandler(
            Filters.location,
            handle_users_reply,
            edited_updates=True
        )
    )
    updater.start_polling()
    logger.info('The bot is running')


if __name__ == '__main__':
    run_bot()
