class PublishMessageError(Exception):
    def __init__(self, msg=str()):
        self.msg = msg
        super(PublishMessageError, self).__init__(self.msg)


class MessageValidationError(PublishMessageError):
    pass


class MessageAuthenticationError(PublishMessageError):
    pass


class ResourceNotFoundError(PublishMessageError):
    pass


class CoordinatorCommunicationError(PublishMessageError):
    pass
