import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiException

from exceptions import APIRequestError, APIResponseError

load_dotenv()

PRACTICUM_TOKEN: str | None = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str | None = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str | None = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)


def check_tokens() -> list[str]:
    """Проверяет доступность обязательных переменных окружения.

    Returns:
        list[str]: Список отсутствующих переменных окружения.
    """
    required_vars = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    return [name for name, value in required_vars.items() if not value]


def send_message(bot: TeleBot, message: str) -> None:
    """Отправляет сообщение в Telegram.

    Args:
        bot: Экземпляр бота TeleBot.
        message: Текст сообщения для отправки.
    """
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    logger.debug(f'Сообщение отправлено: "{message}".')


def get_api_answer(timestamp: int) -> dict:
    """Выполняет запрос к API Практикума для получения статуса домашней работы.

    Args:
        timestamp: Временная метка для запроса

    Returns:
        dict: Ответ API в формате JSON, содержащий:
            - homeworks: Список домашних работ
            - current_date: Текущая дата в формате timestamp

    Raises:
        APIRequestError: Ошибка при выполнении запроса
        APIResponseError: Ошибка в ответе от API
    """
    params = {'from_date': timestamp}
    try:
        logger.debug(
            'Отправка запроса к API.\n'
            f'• Эндпоинт: {ENDPOINT}\n'
            f'• Параметры: {params}\n'
            f'• Заголовки: {
                {k: '***'
                 if k == 'Authorization'
                 else v for k, v in HEADERS.items()}
            }'
        )
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
        if response.status_code != HTTPStatus.OK:
            raise APIResponseError(
                f'Ошибка запроса: {response.status_code} — {response.text}.'
            )

        return response.json()

    except requests.RequestException as error:
        raise APIRequestError(f'Ошибка соединения: {error}.')


def check_response(response: dict) -> None:
    """Проверяет корректность ответа API.

    Args:
        response: Ответ API для проверки.

    Raises:
        TypeError: Если структура ответа не соответствует ожидаемой.
        KeyError: Если отсутствуют обязательные ключи.
    """
    if not isinstance(response, dict):
        raise TypeError('Ответ API должен быть словарём.')

    if 'homeworks' not in response:
        raise KeyError('Отсутствует ключ "homeworks" в ответе API.')
    if not isinstance(response['homeworks'], list):
        raise TypeError('homeworks должен быть списком.')

    if 'current_date' not in response:
        raise KeyError('Отсутствует ключ "current_date" в ответе API.')
    if not isinstance(response['current_date'], int):
        raise TypeError('current_date должен быть целым числом.')


def parse_status(homework: dict) -> str:
    """Извлекает статус домашней работы.

    Args:
        homework: Словарь с информацией о домашней работе.

    Returns:
        str: Форматированное сообщение о статусе работы.

    Raises:
        KeyError: Если отсутствуют обязательные ключи.
        ValueError: Если статус неизвестен.
    """
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует ключ "homework_name" в homework.')

    if 'status' not in homework:
        raise KeyError('Отсутствует ключ "status" в homework.')

    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус: {status}.')

    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    missing_tokens = check_tokens()
    if missing_tokens:
        logger.critical(
            (
                'Отсутствуют обязательные переменные окружения: '
                f'{", ".join(missing_tokens)}.'
            )
        )
        sys.exit(
            'Программа остановлена из-за отсутствия переменных окружения.'
        )

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None

    while True:
        try:
            response = get_api_answer(timestamp)

            check_response(response)
            homeworks = response['homeworks']

            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Нет новых статусов домашних работ.'

            if message != last_message:
                try:
                    send_message(bot, message)
                except ApiException as error:
                    logger.error(f'Ошибка при отправке сообщения: {error}.')
                else:
                    last_message = message
                    timestamp = response.get('current_date', timestamp)

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.error(error_message)
            if error_message != last_message:
                send_message(bot, error_message)
                last_message = error_message

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(message)s',
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    main()
