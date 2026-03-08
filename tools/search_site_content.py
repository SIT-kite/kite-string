from __future__ import annotations

import argparse
import os
from textwrap import shorten

import psycopg
from dotenv import load_dotenv

load_dotenv('.env')


def load_db_parameters() -> dict[str, str | int]:
    return {
        'dbname': os.getenv('PG_DATABASE', 'db'),
        'user': os.getenv('PG_USERNAME', os.getenv('PG_USER', 'postgres')),
        'password': os.getenv('PG_PASSWORD', ''),
        'host': os.getenv('PG_HOST', '127.0.0.1'),
        'port': int(os.getenv('PG_PORT', '5432')),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Search indexed pages and attachments in PostgreSQL.')
    parser.add_argument('query', help='Search query text')
    parser.add_argument('--host', default=None, help='Filter by host')
    parser.add_argument('--attachment-ext', default=None, help='Filter attachments by extension, such as pdf')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of rows')
    parser.add_argument('--offset', type=int, default=0, help='Pagination offset')
    parser.add_argument('--pages-only', action='store_true', help='Search only pages')
    parser.add_argument('--attachments-only', action='store_true', help='Search only attachments')
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    include_pages = not arguments.attachments_only
    include_attachments = not arguments.pages_only

    sql = '''
        SELECT
            source_type,
            source_key,
            title,
            host,
            path,
            ext,
            publish_date,
            referer,
            status,
            rank,
            snippet
        FROM public.search_site_content(%s, %s, %s, %s, %s, %s, %s)
    '''

    with psycopg.connect(**load_db_parameters()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    arguments.query,
                    arguments.host,
                    arguments.attachment_ext,
                    arguments.limit,
                    arguments.offset,
                    include_pages,
                    include_attachments,
                ),
            )
            rows = cursor.fetchall()

    for row in rows:
        source_type, source_key, title, host, path, ext, publish_date, referer, status, rank, snippet = row
        print(f'[{source_type}] {title or "<no-title>"}')
        print(f'  key: {source_key}')
        print(f'  host: {host}')
        print(f'  path: {path}')
        if ext:
            print(f'  ext: {ext}')
        if publish_date:
            print(f'  publish_date: {publish_date}')
        if status:
            print(f'  status: {status}')
        print(f'  rank: {rank:.4f}')
        if referer:
            print(f'  referer: {shorten(referer, width=120, placeholder="...")}')
        if snippet:
            print(f'  snippet: {shorten(snippet.replace(chr(10), " "), width=120, placeholder="...")}')
        print()


if __name__ == '__main__':
    main()
