# -*- coding: utf-8 -*-
# @Time    : 2021/2/21 17:50
# @Author  : sunnysab
# @File    : __init__.py

from typing import List, Tuple
from urllib.parse import parse_qs

import scrapy


def filter_links(link_list: List[Tuple]) -> List[Tuple]:
    """
    Filter links which starts with 'javascript:' and so on.
    :param link_list: Original list to filter.
    :return: A filtered link list.
    """
    forbidden_link_prefix_set = {
        # Some are from https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/a
        '#', 'javascript:', 'mailto:', 'file:', 'ftp:', 'blob:', 'data:'
    }

    def is_forbidden_url(url: str) -> bool:
        for prefix in forbidden_link_prefix_set:
            if url.startswith(prefix):
                return True
        return False

    return [(title, url) for title, url in link_list if not is_forbidden_url(url)]


def get_links(response: scrapy.http.Response) -> List[Tuple[str or None, str]]:
    """
    Get links in the page.
    :param response: A scrapy.http.Response that contains the page
    :return: A list of tuple (title, url)
    """
    link_list = [(a_node.xpath('string(.)').get(), a_node.attrib['href'])  # Make a tuple of title, href
                 for a_node in response.css('a[href]')]
    return filter_links(link_list)


def get_images(response: scrapy.http.Response) -> List[Tuple[str or None, str]]:
    """
    Get image links in the page.
    :param response: A scrapy.http.Response that contains the page.
    :return: A list of tuple (alt, src).
    """
    image_list = [(img_node.attrib.get('alt'), img_node.attrib['src']) for img_node in response.css('img[src]')]
    return filter_links(image_list)


def guess_link_type(path: str) -> str:
    """
    Guess link type by path
    :param path: Path in url.
    :return: 'page' if it seems like a page.
             'attachment' if it seems like an attachment.
             'unknown' if we don't know.
    """

    page_postfix_set = {
        'asp', 'aspx', 'jsp', 'psp', 'do', 'htm', 'html', 'php', 'cgi', '/', 'portal', 'action'
    }

    attachment_postfix_set = {
        # '7z', 'zip', 'rar',
        'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'pdf'
    }

    image_postfix_set = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tif', 'tiff'
    }

    raw_path = (path or '').lower()
    if '#' in raw_path:
        raw_path = raw_path.split('#', 1)[0]

    normalized_path, _, query = raw_path.partition('?')

    query_params = parse_qs(query, keep_blank_values=True)

    def detect_extension(value: str | None) -> str:
        if not value:
            return ''

        extension = value.strip().lower()
        if extension.startswith('.'):
            extension = extension[1:]
        return extension

    query_extension = ''
    for key in ('e', 'ext', 'extension', 'suffix'):
        values = query_params.get(key)
        if values:
            query_extension = detect_extension(values[0])
            if query_extension:
                break

    if 'urltype' in query_params:
        for value in query_params['urltype']:
            if 'downloadattachurl' in value:
                return 'attachment'

    if 'wbfileid' in query_params:
        return 'attachment'

    if query_extension in attachment_postfix_set:
        return 'attachment'

    if query_extension in image_postfix_set:
        return 'image'

    for each_postfix in page_postfix_set:
        if normalized_path.endswith(each_postfix):
            return 'page'

    for each_postfix in attachment_postfix_set:
        if normalized_path.endswith(each_postfix):
            return 'attachment'

    for each_postfix in image_postfix_set:
        if normalized_path.endswith(each_postfix):
            return 'image'

    return 'unknown'
