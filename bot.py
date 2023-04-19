import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

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
    if PRACTICUM_TOKEN is None:
        logging.critical(f'{NONE_TOKEN_MSG} PRACTICUM_TOKEN')
        raise SystemExit
    if TELEGRAM_TOKEN is None:
        logging.critical(f'{NONE_TOKEN_MSG} TELEGRAM_TOKEN')
        raise SystemExit
    if TELEGRAM_CHAT_ID is None:
        logging.critical(f'{NONE_TOKEN_MSG} TELEGRAM_CHAT_ID')
        raise SystemExit


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено в чат')
    except Exception:
        logging.error('Сбой при отправке сообщения в чат')


def get_api_answer(timestamp):
    """Запрос к единственному эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
        status = homework_statuses.status_code
        if status == HTTPStatus.OK:
            homework_result = homework_statuses.json()
            return homework_result
        else:
            logging.error('Ошибка запроса')
            send_message('Ошибка запроса')
            raise ValueError(homework_statuses.json())
    except Exception:
        logging.error('Сбой в работе эндпоинта')
        raise ValueError('Сбой в работе эндпоинта')


def check_response(response):
    """Проверка ответа API и возврат список домашних работ."""
    if isinstance(response, dict) is False:
        logging.error('ответ API не в виде словаря')
        raise TypeError
    if 'homeworks' not in response:
        logging.error('Ожидаемый ключ homeworks отсутствует в ответе API')
        raise KeyError
    if isinstance(response['homeworks'], list) is False:
        logging.error('Ответ API "homeworks" не список')
        raise TypeError
    if 'current_date'not in response:
        logging.error('Ожидаемый ключ current_date отсутствует в ответе API')
        raise KeyError
    if type(response) is None:
        logging.error('Данные получены с типом None')
        raise TypeError


def parse_status(homework):
    """Извлечение статуса работы о конкретной домашней работе."""
    try:
        homework_name = str(homework['homework_name'])
    except Exception:
        logging.error('Не удалось узнать название работы')
    try:
        homework_status = homework['status']
    except Exception:
        logging.error('Не удалось узнать статус работы')
    if homework_status == 'approved':
        verdict = str(HOMEWORK_VERDICTS[homework_status])
        return str(
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
    elif homework_status == 'reviewing':
        verdict = str(HOMEWORK_VERDICTS[homework_status])
        return str(
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
    elif homework_status == 'rejected':
        verdict = str(HOMEWORK_VERDICTS[homework_status])
        return str(
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
    else:
        logging.error('Не обнаружен статус домашней робаты')
        raise KeyError


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logging.critical(
            'Переменные окружения отсутствуют и бот был остановлен'
        )
        exit()
    else:
        logging.info('Бот запущен')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time() - 1814400)
    old_status = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            new_status = parse_status(response['homeworks'][0])
            if new_status != old_status:
                send_message(bot, new_status)
                old_status = new_status
            logger.info(
                'Изменений нет, ждем и проверяем API')
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
