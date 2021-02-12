from typing import Tuple
from urllib.parse import urlparse


def divide_url(url: str) -> Tuple[str, str]:
    """
    Given a full url and return a tuple of host and path.
    Parser is provided by urllib.
    :param url: a full url like 'http://sit.edu.cn/index.htm'
    :return: a tuple like ('sit.edu.cn', '/index.htm')
    """
    result = urlparse(url)
    host, path = result.netloc, result.path

    if len(path) == 0:
        path = '/'
    return host, path
