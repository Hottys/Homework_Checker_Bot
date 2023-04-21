class MessageSendError(Exception):
    """Ошибка отправки сообщения."""

    pass


class ResponseStatusError(Exception):
    """API недоступен."""

    pass

class ServerSendError(Exception):
    """Запрос не смог отправиться."""

    pass

class JSONСonverionError(Exception):
    """Ошибка преобразования в JSON."""

    pass