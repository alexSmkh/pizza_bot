# Pizza Bot
Телеграм бот для пиццерии, серверная сторона которого реализована на
 [Moltin](https://www.moltin.com/).

## Пример работы бота:
![](bot_sample.gif)
 
## Как настроить для работы с Telegram
* Создайте файл `.env` и положите в папку со скриптами
* Создать бота и получить токен
* Записать токен в `.env`
* Записать свой id в `.env`, чтобы бот отправлял вам логи. Узнать id можно у бота 
`@userinfobot`
* Прикрутите к боту платежную систему. Напишите `@BotFather > /mybots > выберите бота > Payment`.
 Получив токен, запишите его в `.env`
* Команда `/start`, чтобы запустить бота
```text
TELEGRAM_TOKEN=token
DEVELOPER_ID=id
PROVIDER_TOKEN=payment_token
```

## Как настроить для Moltin 
* Зарегистрируйтесь на [Moltin](https://www.moltin.com)
* Запишите `Client ID` и `Client secret` в `.env`
```text
MOLTIN_CLIENT_ID=client_id
MOLTIN_CLIENT_SECRET=client_secret
```

## Настройки базы данных(Redis)
* Зарегистрируйтесь и создайте базу данных [Redis](https://redislabs.com/)
* Запишите в `.env` параметры вашей БД
```text
REDIS_HOST=host
REDIS_PORT=port
REDIS_PASSWORD=password
```

## Настройка для сервиса Yandex-Geocoder
* [Зарегистрируйтесь](https://tech.yandex.ru/maps/geocoder/)
* Войдите в "Кабинет разработчика" и получите ключ
* Запишите его в `.env`
```text
GEOCODER_KEY=key
```


## Как запустить 
Для изоляции проекта используйте [VirtualEnv](https://docs.python.org/3/library/venv.html)

Должен быть установлен `Python3` 

Установить зависимости
```bash
pip install -r requirements.txt
```
Загрузить продукты в Moltin
```bash
python load_products_to_moltin.py
```


Запустить бота
```bash
python telegram_bot.py
```

## Развертывание на Heroku
* Создайте приложение
* Запишите переменные окружения из файла `.env`
 в `Settings/Config vars/Reveal Config Vars`
* Выполните развертывание
* Включите нужного вам бота в `Resources/Free Dynos`