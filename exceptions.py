class MessageSendError(Exception):
    """Ошибка отправки сообщения."""

    pass


class ResponseStatusError(Exception):
    """API недоступен."""

    pass

class ServerSendError(Exception):
    """Запрос не смог отправиться."""

    pass

