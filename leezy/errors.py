
import sys
import logging
import requests

LOG = logging.getLogger(__name__)
Info = LOG.info
Debug = LOG.debug
Warn = LOG.warning


def show_error_and_exit(err):
    print(err)
    sys.exit(2)


def raise_for_status(response, description):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        Debug(response.text)
        Debug("\nrequst headers:\n" + str(response.request.headers))
        if e.response.status_code == 403:
            # avoid loop forever during import-time
            from leezy.config import config
            zone = config.get('core.zone')
            assert zone == 'cn' or zone == 'us'
            config.delete("session."+zone)
            raise FetchError(
                "Account authentication failed, you might try again and sign in")
        raise FetchError(description, e)


class LeezyError(Exception):
    def __init__(self, description="", cause=None):
        self.description = description
        self.cause = cause

    def __str__(self):
        display = f'A `{self.__class__.__name__}` occurred'
        if self.description:
            display += '\n information: ' + self.description + '\n'
        if self.cause:
            display += 'caused by:\n'
            display += str(self.cause) + '\n'
        return display


class LoginError(LeezyError):
    pass


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
