import logging
import os
import requests
import sys

from datetime import time
from dotenv import load_dotenv
from telebot import TeleBot


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


logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def check_tokens():
    """Проверяет доступность обязательных переменных окружения."""
    required_vars = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    flag = True
    for name, value in required_vars.items():
        if not value:
            logger.critical(f'Отсутствует переменная окружения {name}.')
            flag = False

    return flag


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение отправлено: {message}.')
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения: {error}.')
        raise


def get_api_answer(timestamp):
    """Запрос к API Практикума."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        response.raise_for_status()
        logger.debug(f'Успешный запрос к API. Код: {response.status_code}.')

        return response.json()

    except Exception as error:
        logger.error(f'Ошибка при запросе к API: {error}.')


def check_response(response):
    """Проверяет корректность ответа API."""
    if not isinstance(response, dict):
        error_message = 'Ответ API должен быть словарём.'
        logger.error(error_message)
        raise TypeError(error_message)

    if 'homeworks' not in response:
        error_message = 'Отсутствует ключ "homeworks" в ответе API.'
        logger.error(error_message)
        raise KeyError(error_message)

    if not isinstance(response['homeworks'], list):
        error_message = 'homeworks должен быть списком.'
        logger.error(error_message)
        raise TypeError(error_message)

    if 'current_date' not in response:
        error_message = 'Отсутствует ключ "current_date" в ответе API.'
        logger.error(error_message)
        raise KeyError(error_message)

    if not isinstance(response['current_date'], int):
        error_message = 'current_date должен быть целым числом.'
        logger.error(error_message)
        raise TypeError(error_message)


def parse_status(homework):
    """Извлекает статус домашней работы."""
    if 'homework_name' not in homework:
        error_message = 'Отсутствует ключ "homework_name" в homework.'
        logger.error(error_message)
        raise KeyError(error_message)

    if 'status' not in homework:
        error_message = 'Отсутствует ключ "status" в homework.'
        logger.error(error_message)
        raise KeyError(error_message)

    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        error_message = f'Неизвестный статус: {status}.'
        logger.error(error_message)
        raise ValueError(error_message)

    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    ...

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
