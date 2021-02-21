# -*- coding: utf-8 -*-
# @Time    : 2021/2/21 14:45
# @Author  : sunnysab
# @File    : auth.py

import requests
from lxml import etree

from aes import *

_LOGIN_URL = 'https://authserver.sit.edu.cn/authserver/login?service=http%3A%2F%2Fmyportal.sit.edu.cn%2F'

_DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/82.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,en-US;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
}


def _hash_password(salt: str, password: str) -> str:
    iv = rds(16)
    encrypt = Encrypt(key=salt, iv=iv)
    hashed_passwd = encrypt.aes_encrypt(rds(64) + password)
    return hashed_passwd


def _get_login_page(session: requests.Session):
    response = session.get(_LOGIN_URL, headers=_DEFAULT_HEADERS, timeout=3)
    response.raise_for_status()

    page = etree.HTML(response.text)
    return page


def _get_login_parameters(page, user: str, passwd: str):
    # Query basic parameters from page.
    form_fields = [
        ('lt', "//input[@name='lt']/@value"),
        ('dllt', "//input[@name='dllt']/@value"),
        ('execution', "//input[@name='execution']/@value"),
        ('_eventId', "//input[@name='_eventId']/@value"),
        ('rmShown', "//input[@name='rmShown']/@value"),
    ]

    result = dict()
    salt = str(page.xpath("//input[@id='pwdDefaultEncryptSalt']/@value")[0])
    for field, xpath_string in form_fields:
        result[field] = str(page.xpath(xpath_string)[0])

    result['username'] = user
    result['password'] = _hash_password(salt, passwd)  # Encrypt password
    return result


def _post_login_request(session: requests.Session, form: dict):
    response = session.post(_LOGIN_URL, data=form, headers=_DEFAULT_HEADERS, timeout=3, allow_redirects=False)
    if response.status_code == 302:  # Login successfully
        return 'OK'
    elif response.status_code == 200:  # Login failed
        error_page = etree.HTML(response.text)
        error_msg = error_page.xpath("//span[@id='msg']/text()")[0]
        return error_msg

    response.raise_for_status()


def login(user: str, passwd: str) -> dict or str:
    session = requests.Session()

    page = _get_login_page(session)
    form = _get_login_parameters(page, user, passwd)
    result = _post_login_request(session, form)
    if result != 'OK':
        session.close()
        return result

    session.close()
    return session.cookies.get_dict('authserver.sit.edu.cn', '/')


if __name__ == '__main__':
    r = login('1234', 'password')
    print(r)
