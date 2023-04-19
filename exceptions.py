class MessageSendError(Exception):
    """Ошибка отправки сообщения."""

    pass

class ServerAnswerError(Exception):
    """Ошибка работы эндпоинта."""

    pass

class RequestError(Exception):
    """Ошибка запроса."""

    pass