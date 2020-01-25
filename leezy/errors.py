
import sys
import requests


def show_error_and_exit(err):
    print(err)
    sys.exit(2)


def raise_for_status(response, description):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FetchError(description, e)


class LeezyError(Exception):
    def __init__(self, description="", cause=None):
        self.description = description
        self.cause = cause

    def __str__(self):
        display = f'A `{self.__class__.__name__}` occurred'
        if self.description:
            display += ': ' + self.description + '\n'
        if self.cause:
            display += 'caused by:\n'
            display += str(self.cause) + '\n'
        return display


class NetworkError(LeezyError):
    pass


class FetchError(LeezyError):
    pass


class NotFound(LeezyError):
    pass


class Locked(LeezyError):
    pass

class ConfigError(LeezyError):
    pass
