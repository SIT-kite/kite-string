from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence
from urllib.parse import urlparse

import botocore.session
import psycopg
from dotenv import load_dotenv

from document_parser import OFFICE_DOCUMENT_EXTENSIONS, UnsupportedAttachmentError, extract_text

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

SUPPORTED_EXTENSIONS = {'pdf', *OFFICE_DOCUMENT_EXTENSIONS}


@dataclass(frozen=True)
class AttachmentRecord:
    id: int
    title: str | None
    ext: str | None
    path: str | None
    local_name: str | None
    checksum: str | None


class AttachmentStore:
    @contextmanager
    def materialize(self, attachment: AttachmentRecord) -> Iterator[Path]:
        raise NotImplementedError


class LocalAttachmentStore(AttachmentStore):
    def __init__(self, base_directory: str):
        self.base_directory = Path(base_directory).expanduser()

    @contextmanager
    def materialize(self, attachment: AttachmentRecord) -> Iterator[Path]:
        if not attachment.local_name:
            raise FileNotFoundError('attachment local_name is empty')

        file_path = self.base_directory / attachment.local_name
        if not file_path.exists():
            raise FileNotFoundError(f'attachment file not found: {file_path}')

        temp_path = ensure_extension(file_path, attachment.ext)
        try:
            yield temp_path
        finally:
            cleanup_temp_file(temp_path, file_path)


class S3AttachmentStore(AttachmentStore):
    def __init__(self, store_uri: str):
        parsed = urlparse(store_uri)
        self.bucket = parsed.netloc
        self.prefix = parsed.path.lstrip('/').rstrip('/')
        session = botocore.session.get_session()
        self.client = session.create_client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID') or None,
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY') or None,
            aws_session_token=os.getenv('AWS_SESSION_TOKEN') or None,
            endpoint_url=os.getenv('AWS_ENDPOINT_URL') or None,
            region_name=os.getenv('AWS_REGION_NAME') or None,
        )

    @contextmanager
    def materialize(self, attachment: AttachmentRecord) -> Iterator[Path]:
        if not attachment.local_name:
            raise FileNotFoundError('attachment local_name is empty')

        suffix = f'.{attachment.ext.lower()}' if attachment.ext else ''
        with tempfile.NamedTemporaryFile(prefix='kite-attachment-', suffix=suffix, delete=False) as temp_file:
            key = attachment.local_name.lstrip('/')
            if self.prefix:
                key = f'{self.prefix}/{key}'
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            with response['Body'] as body:
                shutil.copyfileobj(body, temp_file)
            temp_path = Path(temp_file.name)

        try:
            yield temp_path
        finally:
            cleanup_temp_file(temp_path)


def cleanup_temp_file(path: Path, original_path: Path | None = None):
    if original_path is not None and path == original_path:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def ensure_extension(file_path: Path, extension: str | None) -> Path:
    normalized_extension = (extension or '').lower().lstrip('.')
    if not normalized_extension:
        return file_path
    if file_path.suffix.lower() == f'.{normalized_extension}':
        return file_path

    with open(file_path, 'rb') as source_file:
        with tempfile.NamedTemporaryFile(
            prefix='kite-attachment-',
            suffix=f'.{normalized_extension}',
            delete=False,
        ) as temp_file:
            shutil.copyfileobj(source_file, temp_file)
            return Path(temp_file.name)


def load_db_parameters() -> dict[str, str | int]:
    return {
        'dbname': os.getenv('PG_DATABASE', 'db'),
        'user': os.getenv('PG_USERNAME', os.getenv('PG_USER', 'postgres')),
        'password': os.getenv('PG_PASSWORD', ''),
        'host': os.getenv('PG_HOST', '127.0.0.1'),
        'port': int(os.getenv('PG_PORT', '5432')),
    }


def build_store() -> AttachmentStore:
    files_store = os.getenv('FILES_STORE', 'download').strip()
    if files_store.startswith('s3://'):
        return S3AttachmentStore(files_store)
    return LocalAttachmentStore(files_store)


def load_attachments(
    conn: psycopg.Connection,
    attachment_ids: Sequence[int],
    extensions: Sequence[str],
    limit: int | None,
    force: bool,
    retry_failed: bool,
    retry_skipped: bool,
) -> list[AttachmentRecord]:
    conditions = []
    parameters: list[object] = []

    normalized_extensions = [extension.lower() for extension in extensions]

    if attachment_ids:
        conditions.append('a.id = ANY(%s)')
        parameters.append(list(attachment_ids))

    if normalized_extensions:
        conditions.append('a.ext = ANY(%s)')
        parameters.append(normalized_extensions)
    else:
        conditions.append("lower(COALESCE(a.ext, '')) = ANY(%s)")
        parameters.append(sorted(SUPPORTED_EXTENSIONS))

    if not force:
        retry_statuses = ['pending']
        if retry_failed:
            retry_statuses.append('failed')
        if retry_skipped:
            retry_statuses.append('skipped')
        conditions.append(
            '('
            'ac.attachment_id IS NULL '
            'OR ac.source_checksum IS DISTINCT FROM a.checksum '
            'OR ac.status = ANY(%s)'
            ')'
        )
        parameters.append(retry_statuses)

    where_clause = ''
    if conditions:
        where_clause = 'WHERE ' + ' AND '.join(conditions)

    limit_clause = ''
    if limit is not None:
        limit_clause = 'LIMIT %s'
        parameters.append(limit)

    sql = f'''
        SELECT a.id, a.title, a.ext, a.path, a.local_name, a.checksum
        FROM public.attachments AS a
        LEFT JOIN public.attachment_content AS ac ON ac.attachment_id = a.id
        {where_clause}
        ORDER BY a.id
        {limit_clause}
    '''

    with conn.cursor() as cursor:
        cursor.execute(sql, parameters)
        rows = cursor.fetchall()

    return [AttachmentRecord(*row) for row in rows]


def save_attachment_content(
    conn: psycopg.Connection,
    attachment_id: int,
    content: str,
    content_type: str | None,
    parser: str | None,
    status: str,
    error_message: str | None,
    source_checksum: str | None,
):
    sql = '''
        INSERT INTO public.attachment_content
            (attachment_id, content, content_type, parser, status, error_message, source_checksum, indexed_at)
        VALUES
            (
                %s::integer,
                COALESCE(%s::text, ''),
                %s::text,
                %s::text,
                COALESCE(%s::text, 'pending'),
                %s::text,
                %s::text,
                CASE WHEN COALESCE(%s::text, 'pending') = 'pending' THEN NULL ELSE now() END
            )
        ON CONFLICT (attachment_id)
            DO UPDATE
            SET content = COALESCE(EXCLUDED.content, ''),
                content_type = EXCLUDED.content_type,
                parser = EXCLUDED.parser,
                status = EXCLUDED.status,
                error_message = EXCLUDED.error_message,
                source_checksum = EXCLUDED.source_checksum,
                indexed_at = CASE WHEN EXCLUDED.status = 'pending' THEN public.attachment_content.indexed_at ELSE now() END,
                updated_at = now();
    '''
    with conn.cursor() as cursor:
        cursor.execute(
            sql,
            (
                attachment_id,
                content,
                content_type,
                parser,
                status,
                error_message,
                source_checksum,
                status,
            ),
        )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Index attachment content into PostgreSQL.')
    parser.add_argument('--attachment-id', type=int, action='append', default=[], help='Index only selected id')
    parser.add_argument('--ext', action='append', default=[], help='Index only selected extension')
    parser.add_argument('--limit', type=int, default=100, help='Maximum attachments to process')
    parser.add_argument('--force', action='store_true', help='Reindex matched attachments regardless of checksum')
    parser.add_argument('--retry-failed', action='store_true', help='Retry attachments previously marked failed')
    parser.add_argument('--retry-skipped', action='store_true', help='Retry attachments previously marked skipped')
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    store = build_store()

    with psycopg.connect(**load_db_parameters(), autocommit=True) as conn:
        attachments = load_attachments(
            conn,
            arguments.attachment_id,
            arguments.ext,
            arguments.limit,
            arguments.force,
            arguments.retry_failed,
            arguments.retry_skipped,
        )

        for attachment in attachments:
            content = ''
            content_type = None
            parser_name = None
            status = 'failed'
            error_message = None

            try:
                with store.materialize(attachment) as local_path:
                    extracted = extract_text(str(local_path), attachment.ext)
                    content = extracted.content
                    content_type = extracted.content_type
                    parser_name = extracted.parser

                if content:
                    status = 'success'
                else:
                    status = 'skipped'
                    error_message = 'no text content extracted'
            except UnsupportedAttachmentError as exc:
                status = 'skipped'
                error_message = str(exc)
            except Exception as exc:
                status = 'failed'
                error_message = str(exc)

            save_attachment_content(
                conn,
                attachment.id,
                content,
                content_type,
                parser_name,
                status,
                error_message,
                attachment.checksum,
            )
            print(f'[{status}] #{attachment.id} {attachment.path or attachment.local_name or "<unknown>"}')


if __name__ == '__main__':
    main()
