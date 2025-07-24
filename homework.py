import logging
import os
import sys
import time
from http import HTTPStatus

import requests
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
    format='%(asctime)s [%(levelname)s] %(message)s',
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

    missing_tokens = [
        name for name, value in required_vars.items() if not value
    ]
    flag = True
    if missing_tokens:
        logger.critical(
            f'Отсутствуют обязательные переменные окружения: {
                ", ".join(missing_tokens)
            }.'
        )
        flag = False
    return flag


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Сообщение отправлено: "{message}".')
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения: {error}.')


def get_api_answer(timestamp):
    """Запрос к API Практикума."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            raise Exception(
                f'Ошибка запроса: {response.status_code} — {response.text}'
            )
        return response.json()

    except requests.RequestException as error:
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
        error_message = f'Неизвестный статус: {status}'
        logger.error(error_message)
        raise ValueError(error_message)

    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(
            'Программа остановлена из-за отсутствия переменных окружения.'
        )

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error = None

    while True:
        try:
            response = get_api_answer(timestamp)

            check_response(response)
            homeworks = response['homeworks']

            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logger.debug('Нет новых статусов домашних работ.')

            timestamp = response.get('current_date', timestamp)

            last_error = None

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.error(error_message)
            if str(error) != last_error:
                send_message(bot, error_message)
                last_error = str(error)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
