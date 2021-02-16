# -*- coding: utf-8 -*-
# @Time    : 2021/2/16 7:16
# @Author  : sunnysab
# @File    : update-content.py
#
# Use urls exported from postgresql and re-request, re-parse content.
#

import asyncio
import time
from typing import List, Dict, Tuple
from urllib.parse import urlparse

import aiohttp
import asyncpg
import cchardet
from lxml import etree
from readability import Document

sessions: Dict[str, aiohttp.ClientSession] = dict()


def get_session(domain: str) -> aiohttp.ClientSession:
    if domain not in sessions:
        sessions[domain] = aiohttp.ClientSession()
    return sessions[domain]


def divide_url(url: str) -> Tuple[str, str]:
    result = urlparse(url)
    host, path = result.netloc, result.path

    if len(path) == 0:
        path = '/'
    return host, path


def load_urls(file: str = 'urls.txt') -> List[str]:
    r = open(file, 'r', encoding='utf-8').readlines()
    return [line.rstrip() for line in r if line]


async def request(url: str) -> bytes or None:
    host, _ = divide_url(url)
    session = get_session(host)

    async with session.get(url, allow_redirects=True) as response:
        if response.status != 200:
            return None
        html = await response.read()

    return html


def process_content(body: bytes) -> Tuple[str, str]:
    def clean(s) -> str:
        return s.replace('\xa0', ' ').strip()

    try:
        encoding = 'utf-8'
        html = body.decode(encoding)
    except Exception as _:
        encoding = cchardet.detect(body)['encoding']
        html = body.decode(encoding, errors='replace')

    doc = Document(html)
    page = etree.HTML(doc.summary())
    paragraphs = [clean(p.xpath('string(.)')) for p in page.xpath('//p')]

    return doc.title(), '\n'.join(paragraphs)


async def create_db_pool() -> asyncpg.Pool:
    parameters = {
        'database': 'db',
        'user': 'postgres',
        'password': '我不告诉你',
        'host': '192.168.50.101'
    }
    return await asyncpg.create_pool(**parameters)


async def update_content(pool: asyncpg.Pool,
                         url: str, title: str, content: str):
    sql = \
        f'''
        -- update_page(_host text, _path text, _title text, _content text)

        CALL public.update_page($1, $2, $3, $4);
        '''
    host, path = divide_url(url)
    await pool.execute(sql, host, path, title, content)


async def main():
    pool = await create_db_pool()
    urls = load_urls()
    i = 0

    s_time = time.time()
    print(f'start at {s_time}')
    for u in urls:
        try:
            body = await request(u)
            title, content = process_content(body)
            await update_content(pool, u, title, content)
        except Exception as e:
            print(f'Error while processing {u}\n  type: {type(e)}\n  detail: {e}')

        i += 1
        if i % 100 == 0:
            print(i)
    print(f'end at {time.time()}, {time.time() - s_time} s elapsed.')


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
