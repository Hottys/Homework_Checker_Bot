import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler
from exceptions import (
    MessageSendError,
    ResponseStatusError,
    ServerSendError
)

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Проверка доступности переменных окружения."""
    NONE_TOKEN_MSG = (
        'Бот остановлен. Отсутствует обязательный токен'
    )
    for tokens in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        if tokens is None:
            logging.critical(f'{NONE_TOKEN_MSG} - {tokens}')
            raise sys.exit(1)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        logging.info('Начало отправки сообщения в Telegram')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logging.error(
            'Сбой при отправке сообщения в чат'
        )
        raise MessageSendError('Сбой при отправке сообщения в чат')
    else:
        logging.debug('Сообщение отправлено в чат')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API-сервиса."""
    logging.info('Начало запроса к API')
    payload = {'from_date': timestamp}
    try:
        homework_response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
        status = homework_response.status_code
        if status != HTTPStatus.OK:
            raise ResponseStatusError('API недоступен')
        return homework_response.json()
    except Exception:
        raise ServerSendError('Запрос не смог отправиться')


def check_response(response):
    """Проверка ответа API и возврат список домашних работ."""
    logging.info('Начало проверки ответа от сервера')
    if not isinstance(response, dict):
        raise TypeError('Ответ API не в виде словаря')
    if 'homeworks' not in response:
        raise KeyError('Ожидаемый ключ homeworks отсутствует в ответе API')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Ответ API "homeworks" не список')
    if 'current_date'not in response:
        raise KeyError('Ожидаемый ключ current_date отсутствует в ответе API')
    return response['homeworks']


def parse_status(homework):
    """Извлечение статуса работы о конкретной домашней работе."""
    logging.info('Начало извлечения статуса дз')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        raise KeyError('Не обнаружено имя homework_name')
    if 'status' not in homework:
        raise KeyError('Не обнаружен ключ status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Не обнаружен статус домашней робаты')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return (
        f'Изменился статус проверки работы "{homework_name}". {verdict}'
    )


def main():
    """Основная логика работы бота."""
    logging.info('Бот запущен')
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    check_last_message = ''
    old_status = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            new_status = response['homeworks'][0]
            if new_status:
                if new_status != old_status:
                    send_message(bot, parse_status(new_status))
                    old_status = new_status
                timestamp = response.get('current_date')
        except MessageSendError as message_error:
            logging.error(
                f'Сбой при отправке сообщения в чат {message_error}'
            )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if check_last_message != message:
                send_message(bot, message)
                check_last_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
