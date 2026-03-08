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
    parser = argparse.ArgumentParser(description='Search indexed attachments in PostgreSQL.')
    parser.add_argument('query', help='Search query text')
    parser.add_argument('--ext', default=None, help='Filter by extension, such as pdf or docx')
    parser.add_argument('--host', default=None, help='Filter by host')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of rows')
    parser.add_argument('--offset', type=int, default=0, help='Pagination offset')
    parser.add_argument('--metadata-only', action='store_true', help='Search metadata only, ignore full text')
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    sql = '''
        SELECT
            attachment_id,
            title,
            ext,
            host,
            path,
            referer,
            status,
            metadata_rank,
            content_rank,
            rank,
            snippet
        FROM public.search_attachment(%s, %s, %s, %s, %s, %s)
    '''

    with psycopg.connect(**load_db_parameters()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    arguments.query,
                    arguments.ext,
                    arguments.host,
                    arguments.limit,
                    arguments.offset,
                    not arguments.metadata_only,
                ),
            )
            rows = cursor.fetchall()

    for row in rows:
        attachment_id, title, ext, host, path, referer, status, metadata_rank, content_rank, rank, snippet = row
        print(f'#{attachment_id} [{ext}] {title or "<no-title>"}')
        print(f'  host: {host}')
        print(f'  path: {path}')
        print(f'  status: {status or "<none>"}')
        print(f'  rank: {rank:.4f} (meta={metadata_rank:.4f}, content={content_rank:.4f})')
        if referer:
            print(f'  referer: {shorten(referer, width=120, placeholder="...")}')
        if snippet:
            print(f'  snippet: {shorten(snippet.replace(chr(10), " "), width=120, placeholder="...")}')
        print()


if __name__ == '__main__':
    main()
