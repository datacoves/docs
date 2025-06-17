class SecretsBackend:
    def __init__(self, project):
        self.project = project

    def get(cls, secret) -> dict:
        raise NotImplementedError()

    def create(cls, secret, value):
        raise NotImplementedError()

    def update(cls, secret, value):
        raise NotImplementedError()

    def delete(cls, secret):
        raise NotImplementedError()


class SecretNotFoundException(Exception):
    pass


class SecretAlreadyExistsException(Exception):
    pass
