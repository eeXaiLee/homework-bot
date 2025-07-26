class APIRequestError(Exception):
    """Кастомное исключение для ошибок запроса к API."""

    pass


class APIResponseError(Exception):
    """Кастомное исключение для ошибок ответа от API."""

    pass
