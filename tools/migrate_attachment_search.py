from __future__ import annotations

import os

import psycopg
from dotenv import load_dotenv

load_dotenv('.env')

SQL = r'''
CREATE EXTENSION IF NOT EXISTS pg_jieba;

ALTER TABLE public.attachments
ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_attachments_ext_index
    ON public.attachments (ext);

CREATE INDEX IF NOT EXISTS idx_attachments_search_vector
    ON public.attachments USING gin (search_vector);

CREATE TABLE IF NOT EXISTS public.attachment_content
(
    attachment_id   integer                     not null
        constraint attachment_content_pk
            primary key
        constraint attachment_content_attachment_id_fk
            references public.attachments(id)
                on delete cascade,
    content         text        default ''::text not null,
    content_type    text,
    parser          text,
    status          text        default 'pending'::text not null,
    error_message   text,
    source_checksum char(32),
    indexed_at      timestamptz,
    updated_at      timestamptz default now() not null,
    search_vector   tsvector
);

ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS content text default ''::text not null;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS content_type text;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS parser text;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS status text default 'pending'::text not null;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS error_message text;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS source_checksum char(32);
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS indexed_at timestamptz;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS updated_at timestamptz default now() not null;
ALTER TABLE public.attachment_content
ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_attachment_content_search_vector
    ON public.attachment_content USING gin (search_vector);
CREATE INDEX IF NOT EXISTS idx_attachment_content_status_index
    ON public.attachment_content (status);

CREATE OR REPLACE FUNCTION public.extract_attachment_filename(
    _path text,
    _local_name text
) RETURNS text AS
$$
SELECT COALESCE(
    NULLIF(regexp_replace(split_part(COALESCE(_path, ''), '?', 1), '^.*/', ''), ''),
    NULLIF(regexp_replace(COALESCE(_local_name, ''), '^.*/', ''), ''),
    ''
);
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION public.build_attachment_metadata_search_vector(
    _title text,
    _path text,
    _local_name text,
    _ext text,
    _referer text
) RETURNS tsvector AS
$$
SELECT
    setweight(to_tsvector('jiebaqry', COALESCE(_title, '')), 'A') ||
    setweight(
        to_tsvector('jiebaqry', public.extract_attachment_filename(_path, _local_name)),
        'A'
    ) ||
    setweight(to_tsvector('jiebaqry', COALESCE(_ext, '')), 'B') ||
    setweight(to_tsvector('jiebaqry', COALESCE(_referer, '')), 'B');
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION public.build_attachment_search_vector(
    _title text,
    _content text
) RETURNS tsvector AS
$$
SELECT
    setweight(to_tsvector('jiebaqry', COALESCE(_title, '')), 'A') ||
    setweight(
        to_tsvector('jiebaqry', COALESCE(SUBSTRING(_content FROM 1 FOR 50000), '')),
        'B'
    );
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION public.search_attachment(
    _query text,
    _ext text DEFAULT NULL,
    _host text DEFAULT NULL,
    _limit integer DEFAULT 20,
    _offset integer DEFAULT 0,
    _search_content boolean DEFAULT true
) RETURNS TABLE (
    attachment_id integer,
    title text,
    ext text,
    host text,
    path text,
    referer text,
    status text,
    metadata_rank real,
    content_rank real,
    rank real,
    snippet text
) AS
$$
WITH query_input AS (
    SELECT plainto_tsquery('jiebaqry', COALESCE(NULLIF(btrim(_query), ''), '')) AS ts_query
), candidates AS (
    SELECT
        a.id AS attachment_id,
        a.title,
        a.ext,
        a.host,
        a.path,
        a.referer,
        ac.status,
        ts_rank_cd(a.search_vector, qi.ts_query) AS metadata_rank,
        CASE
            WHEN _search_content THEN ts_rank_cd(ac.search_vector, qi.ts_query)
            ELSE 0::real
        END AS content_rank,
        CASE
            WHEN _search_content AND ac.content IS NOT NULL AND ac.search_vector @@ qi.ts_query
                THEN substring(ac.content FROM 1 FOR 200)
            ELSE NULL
        END AS snippet
    FROM public.attachments AS a
    CROSS JOIN query_input AS qi
    LEFT JOIN public.attachment_content AS ac ON ac.attachment_id = a.id
    WHERE qi.ts_query <> ''::tsquery
      AND (_ext IS NULL OR lower(a.ext) = lower(_ext))
      AND (_host IS NULL OR a.host = _host)
      AND (
            a.search_vector @@ qi.ts_query
            OR (
                _search_content
                AND ac.search_vector IS NOT NULL
                AND ac.search_vector @@ qi.ts_query
            )
      )
)
SELECT
    candidates.attachment_id,
    candidates.title,
    candidates.ext,
    candidates.host,
    candidates.path,
    candidates.referer,
    candidates.status,
    candidates.metadata_rank,
    candidates.content_rank,
    (candidates.metadata_rank + candidates.content_rank) AS rank,
    candidates.snippet
FROM candidates
ORDER BY rank DESC, attachment_id DESC
LIMIT GREATEST(COALESCE(_limit, 20), 1)
OFFSET GREATEST(COALESCE(_offset, 0), 0);
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION public.search_site_content(
    _query text,
    _host text DEFAULT NULL,
    _attachment_ext text DEFAULT NULL,
    _limit integer DEFAULT 20,
    _offset integer DEFAULT 0,
    _include_pages boolean DEFAULT true,
    _include_attachments boolean DEFAULT true
) RETURNS TABLE (
    source_type text,
    source_key text,
    title text,
    host text,
    path text,
    ext text,
    publish_date date,
    referer text,
    status text,
    rank real,
    snippet text
) AS
$$
WITH query_input AS (
    SELECT plainto_tsquery('jiebaqry', COALESCE(NULLIF(btrim(_query), ''), '')) AS ts_query
), page_candidates AS (
    SELECT
        'page'::text AS source_type,
        concat_ws('', p.host, p.path) AS source_key,
        p.title,
        p.host,
        p.path,
        NULL::text AS ext,
        p.publish_date,
        NULL::text AS referer,
        'success'::text AS status,
        ts_rank_cd(p.search_vector, qi.ts_query) AS rank,
        substring(p.content FROM 1 FOR 200) AS snippet
    FROM public.pages AS p
    CROSS JOIN query_input AS qi
    WHERE _include_pages
      AND qi.ts_query <> ''::tsquery
      AND (_host IS NULL OR p.host = _host)
      AND p.search_vector @@ qi.ts_query
), attachment_candidates AS (
    SELECT
        'attachment'::text AS source_type,
        a.id::text AS source_key,
        a.title,
        a.host,
        a.path,
        a.ext,
        NULL::date AS publish_date,
        a.referer,
        sa.status,
        sa.rank,
        sa.snippet
    FROM public.search_attachment(
        _query,
        _attachment_ext,
        _host,
        GREATEST(COALESCE(_limit, 20) + GREATEST(COALESCE(_offset, 0), 0), 20),
        0,
        true
    ) AS sa
    JOIN public.attachments AS a ON a.id = sa.attachment_id
    WHERE _include_attachments
)
SELECT *
FROM (
    SELECT * FROM page_candidates
    UNION ALL
    SELECT * FROM attachment_candidates
) AS combined
ORDER BY rank DESC, source_type ASC, source_key DESC
LIMIT GREATEST(COALESCE(_limit, 20), 1)
OFFSET GREATEST(COALESCE(_offset, 0), 0);
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION public.should_index_attachment_content(
    _ext text
) RETURNS boolean AS
$$
SELECT lower(COALESCE(_ext, '')) = ANY (ARRAY['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']);
$$ LANGUAGE sql IMMUTABLE;

CREATE OR REPLACE FUNCTION public.attachments_search_vector_trigger()
RETURNS trigger AS
$$
BEGIN
    NEW.search_vector = public.build_attachment_metadata_search_vector(
        NEW.title,
        NEW.path,
        NEW.local_name,
        NEW.ext,
        NEW.referer
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.queue_attachment_content_index_trigger()
RETURNS trigger AS
$$
BEGIN
    IF public.should_index_attachment_content(NEW.ext) THEN
        INSERT INTO public.attachment_content (attachment_id, status, source_checksum, updated_at)
        VALUES (NEW.id, 'pending', NEW.checksum, now())
        ON CONFLICT (attachment_id)
            DO UPDATE
            SET status          = CASE
                                      WHEN public.attachment_content.source_checksum IS DISTINCT FROM EXCLUDED.source_checksum
                                          THEN 'pending'
                                      ELSE public.attachment_content.status
                                  END,
                error_message   = CASE
                                      WHEN public.attachment_content.source_checksum IS DISTINCT FROM EXCLUDED.source_checksum
                                          THEN NULL
                                      ELSE public.attachment_content.error_message
                                  END,
                source_checksum = EXCLUDED.source_checksum,
                updated_at      = now();
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.sync_attachment_content_search_vector_trigger()
RETURNS trigger AS
$$
BEGIN
    UPDATE public.attachment_content
    SET search_vector = public.build_attachment_search_vector(NEW.title, content),
        updated_at = now()
    WHERE attachment_id = NEW.id
      AND status = 'success';

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.attachment_content_search_vector_trigger()
RETURNS trigger AS
$$
DECLARE
    _title text;
BEGIN
    NEW.updated_at = now();

    SELECT title
    INTO _title
    FROM public.attachments
    WHERE id = NEW.attachment_id;

    IF NEW.status = 'success' THEN
        NEW.search_vector = public.build_attachment_search_vector(_title, NEW.content);
    ELSE
        NEW.search_vector = NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_attachments_search_vector ON public.attachments;
CREATE TRIGGER trg_attachments_search_vector
BEFORE INSERT OR UPDATE OF title, path, local_name, ext, referer
ON public.attachments
FOR EACH ROW EXECUTE FUNCTION public.attachments_search_vector_trigger();

DROP TRIGGER IF EXISTS trg_sync_attachment_content_search_vector ON public.attachments;
CREATE TRIGGER trg_sync_attachment_content_search_vector
AFTER INSERT OR UPDATE OF title
ON public.attachments
FOR EACH ROW EXECUTE FUNCTION public.sync_attachment_content_search_vector_trigger();

DROP TRIGGER IF EXISTS trg_queue_attachment_content_index ON public.attachments;
CREATE TRIGGER trg_queue_attachment_content_index
AFTER INSERT OR UPDATE OF ext, checksum, local_name
ON public.attachments
FOR EACH ROW EXECUTE FUNCTION public.queue_attachment_content_index_trigger();

DROP TRIGGER IF EXISTS trg_attachment_content_search_vector ON public.attachment_content;
CREATE TRIGGER trg_attachment_content_search_vector
BEFORE INSERT OR UPDATE OF attachment_id, content, status
ON public.attachment_content
FOR EACH ROW EXECUTE FUNCTION public.attachment_content_search_vector_trigger();

UPDATE public.attachments
SET search_vector = public.build_attachment_metadata_search_vector(title, path, local_name, ext, referer)
WHERE search_vector IS NULL;

UPDATE public.attachment_content AS ac
SET search_vector = public.build_attachment_search_vector(a.title, ac.content)
FROM public.attachments AS a
WHERE ac.attachment_id = a.id
  AND ac.status = 'success';

INSERT INTO public.attachment_content (attachment_id, status, source_checksum, updated_at)
SELECT a.id, 'pending', a.checksum, now()
FROM public.attachments AS a
LEFT JOIN public.attachment_content AS ac ON ac.attachment_id = a.id
WHERE public.should_index_attachment_content(a.ext)
  AND ac.attachment_id IS NULL;
'''


def main():
    conn = psycopg.connect(
        dbname=os.getenv('PG_DATABASE', 'db'),
        user=os.getenv('PG_USERNAME', os.getenv('PG_USER', 'postgres')),
        password=os.getenv('PG_PASSWORD', ''),
        host=os.getenv('PG_HOST', '127.0.0.1'),
        port=int(os.getenv('PG_PORT', '5432')),
        autocommit=True,
    )
    with conn, conn.cursor() as cursor:
        cursor.execute(SQL)
    print('attachment search migration applied')


if __name__ == '__main__':
    main()
