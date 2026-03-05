/*
    注意，这不是一个可以直接导入的 SQL 文件。

    你需要先执行下面创建数据的语句，并确保 PostgreSQL 已安装 pg_jieba 扩展。

    如果想快速体验且暂不安装 pg_jieba，请删除索引 idx_pages_search_vector 创建行。
    如果有其他问题，可以在仓库中提一个 issue：
    https://github.com/sunnysab/kite-string/issues

    2021.2.14  @sunnysab
*/

/* DATABASE */
CREATE DATABASE kite;

/* EXTENSIONS */
CREATE EXTENSION IF NOT EXISTS pg_jieba;


/* TABLES */

CREATE TABLE IF NOT EXISTS attachments
(
    id         serial                not null
        constraint attachments_pk
            primary key,
    title      text,
    host       text,
    path       text,
    ext        text,
    size       integer,
    local_name text,
    checksum   char(32),
    referer    text default ''::text not null
);
COMMENT ON TABLE attachments IS '附件列表';

CREATE UNIQUE INDEX idx_attachments_host_path_index
    ON attachments (host, path);


CREATE TABLE IF NOT EXISTS pages
(
    title        text,
    host         text,
    path         text,
    publish_date date,
    update_date  date,
    link_count   smallint,
    content      text not null,
    search_vector tsvector
);
COMMENT ON TABLE pages IS '爬取到的文章';

ALTER TABLE pages
ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE UNIQUE INDEX idx_pages_host_path_index
    ON pages (host, path);

CREATE OR REPLACE FUNCTION public.build_page_search_vector(
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

CREATE OR REPLACE FUNCTION public.pages_search_vector_trigger()
RETURNS trigger AS
$$
BEGIN
    NEW.search_vector = public.build_page_search_vector(NEW.title, NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pages_search_vector ON pages;

CREATE TRIGGER trg_pages_search_vector
BEFORE INSERT OR UPDATE OF title, content
ON pages
FOR EACH ROW EXECUTE FUNCTION public.pages_search_vector_trigger();

UPDATE pages
SET search_vector = public.build_page_search_vector(title, content)
WHERE search_vector IS NULL;

DROP INDEX IF EXISTS idx_gin_page_content;

-- 倒排索引
CREATE INDEX IF NOT EXISTS idx_pages_search_vector
    ON pages USING gin (search_vector);

CREATE INDEX IF NOT EXISTS pages_publish_date_index
    ON pages (publish_date DESC);

/*
    FUNCTIONS AND PROCEDURES
*/

-- Save page
CREATE OR REPLACE PROCEDURE public.submit_page(
    _title text,
    _host text,
    _path text,
    _publish_date date,
    _link_count integer,
    _content text
) AS
$$
BEGIN
    INSERT INTO public.pages (title, host, path, publish_date, link_count, content)
    VALUES (_title, _host, _path, _publish_date, _link_count, _content)
    ON CONFLICT (host, path)
        DO UPDATE
        SET title        = _title,
            publish_date = _publish_date,
            link_count   = _link_count,
            content      = _content;
END;
$$ LANGUAGE plpgsql;

-- Update existing page content by host/path.
CREATE OR REPLACE PROCEDURE public.update_page(
    _host text,
    _path text,
    _title text,
    _content text
) AS
$$
BEGIN
    UPDATE public.pages
    SET title   = _title,
        content = _content
    WHERE host = _host
      AND path = _path;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE PROCEDURE public.submit_attachment(
    _title text,
    _host text,
    _path text,
    _ext text,
    _size integer,
    _local_name text,
    _checksum text,
    _referer text
) AS
$$
BEGIN
    INSERT INTO public.attachments (title, host, path, ext, size, local_name, checksum, referer)
    VALUES (_title, _host, _path, _ext, _size, _local_name, _checksum, _referer)
    ON CONFLICT (host, path)
        DO UPDATE
        SET title      = _title,
            ext        = _ext,
            size       = _size,
            local_name = _local_name,
            checksum   = _checksum,
            referer    = _referer;
END;
$$ LANGUAGE plpgsql;
