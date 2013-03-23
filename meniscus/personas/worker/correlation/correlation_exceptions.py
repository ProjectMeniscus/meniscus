class PublishMessageError(Exception):
    def __init__(self, message=str()):
        self.message = message


class MessageValidationError(PublishMessageError):
    pass


class MessageAuthenticationError(PublishMessageError):
    pass


class ResourceNotFoundError(PublishMessageError):
    pass


class CoordinatorCommunicationError(PublishMessageError):
    pass


