/*
    注意，这不是一个可以直接导入的 SQL 文件。

    你需要先执行下面创建数据的语句，然后配置中文分词扩展 zhparser。
    这儿有一篇资料：
    https://sunnysab.cn/2021/02/13/Configure-Zhparser-On-Postgresql.md/

    配置过程有些繁琐。如果想快速体验，请删除索引 idx_gin_page_content 创建行。
    如果有其他问题，可以在仓库中提一个 issue：
    https://github.com/sunnysab/kite-string/issues

    2021.2.14  @sunnysab
*/

/* DATABASE */
CREATE DATABASE kite;


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
    ON attachments (HASHTEXT(host || path));


CREATE TABLE IF NOT EXISTS pages
(
    title        text,
    host         text,
    path         text,
    publish_date date,
    update_date  date,
    link_count   smallint,
    content      text not null
);
COMMENT ON TABLE pages IS '爬取到的文章';

CREATE UNIQUE INDEX idx_pages_host_path_index
    ON pages (HASHTEXT(host || path));

-- 倒排索引
CREATE INDEX IF NOT EXISTS idx_gin_page_content
    ON pages USING gin (to_tsvector('kite_web'::regconfig, content));

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
    ON CONFLICT (HASHTEXT(host || path))
        DO UPDATE
        SET title        = _title,
            publish_date = _publish_date,
            link_count   = _link_count,
            content      = _content;
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
    ON CONFLICT (HASHTEXT(host || path))
        DO UPDATE
        SET title      = _title,
            ext        = _ext,
            size       = _size,
            local_name = _local_name,
            checksum   = _checksum,
            referer    = _referer;
END;
$$ LANGUAGE plpgsql;
