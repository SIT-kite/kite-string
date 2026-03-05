# kite-string 校园网全站爬虫

本项目是一个基于 Scrapy 框架下的爬虫脚本，旨在抓取校园网各页面，并索引进数据库。

爬虫范围：

- [x] 公开页面

该项目作为 [上应小风筝](https://github.com/SIT-Yiban/kite-microapp) 的一部分发布。 爬虫将缓存站点网页内容和一些小一点的附件，以供后续为用户提供校园网内的文件、网页检索服务。

项目爬虫部分的三名作者曾经有过一些 Python 语言的经验，但是均为第一次接触 Scrapy 框架。 而公开页面爬虫与网上流行的针对特定条目、字段进行爬取的示例不同，本项目作为一个通用的爬虫脚本， 因而作者在探索优雅地基于 Scrapy 框架编写整站爬虫过程中，踩过不少坑。
限于精力，当前版本的项目，存在一定的效率问题，（可能）将在今后不断地改善。

该项目为 [上海应用技术大学-网站](https://www.sit.edu.cn/) 设计，不保证对其他站点有效。

## 开发环境

主要开发和生产环境软件（及语言库）版本如下：

- Windows 10
- Ubuntu 20.04 LTS
- FreeBSD 12.2
- Python 3.7, 3.9
- Scrapy 2.4.1
- PyCharm 2020.3
- PostgreSQL 13.2
- pg_jieba

## 快速指南

### 配置

请先修改 `kite/settings.py` 的配置选项：

```python
# 数据库配置选项
PG_DATABASE = 'db'
PG_USERNAME = 'user'
PG_PASSWORD = 'password'
PG_PORT = 5432
PG_HOST = 'ip'

# 附件存储路径
FILES_STORE = 'download'
```

项目支持自动加载 `.env`（通过 `python-dotenv`），你也可以把这些变量写到仓库根目录 `.env`：

```dotenv
PG_DATABASE=db
PG_USERNAME=user
PG_PASSWORD=password
PG_HOST=127.0.0.1
PG_PORT=5432
FILES_STORE=download
```

如果你希望将附件和图片直接存入 S3，请使用环境变量覆盖：

```shell
export FILES_STORE='s3://your-bucket/kite'
export FILES_STORE_S3_ACL='private'
export AWS_ACCESS_KEY_ID='xxx'
export AWS_SECRET_ACCESS_KEY='xxx'
# 可选：自建对象存储（如 MinIO/Ceph）
export AWS_ENDPOINT_URL='https://s3.example.com'
export AWS_REGION_NAME='ap-east-1'
```

说明：

- 页面正文元信息写入 `pages` 表。
- 附件和图片的元信息统一写入 `attachments` 表。
- 文件实体存储在 `FILES_STORE` 指向的位置（本地目录或 S3）。
- 全文检索使用 `pg_jieba` 的 `jiebaqry` 配置，并维护 `pages.search_vector` 列（`title` 权重 A，`content` 权重 B）。

如有需要，可以在 `kite/spiders/__init__.py` 中修改已知的扩展名列表：

```python
page_postfix_set = {
    'asp', 'aspx', 'jsp', 'do', 'htm', 'html', 'php', 'cgi', '/', 'portal', 'action'
}

attachment_postfix_set = {
    # '7z', 'zip', 'rar',
    'xls', 'xlsx', 'doc', 'docx', 'ppt', 'pptx', 'pdf'
}
```

根据经验，抓取上海应用技术大学网站时，请为下载目录 `FILES_STORE` 预留至少 4GB 空间，并确保数据库路径存有 500MB 空间。

如果您运行 `public` 爬虫，大部分页面是可以在公网访问到的。抓取速度受网络和校方服务器限制，调高 `settings.py` 中并发所带来的收益并不大。

在并发请求数设置为 `128` 的情况下，作者最近一次运行 `public` 爬虫抓取用时约 4 小时，实际并发连接数保持在 100 左右。

截至 README.md 文档修改时，公开网页约 12 万篇（过滤后超 5 万篇），附件近 1 万个。

### 执行方式

执行

```shell
git clone https://github.com/sunnysab/kite-string
cd kite-string

# 安装 uv（如未安装）
# https://docs.astral.sh/uv/getting-started/installation/

# 安装项目依赖
uv sync

# 运行静态检查
uv run --group dev ruff check .

# 如果需要运行 tools/ 下的 PDF 处理脚本，可额外安装 tools 依赖组
uv sync --extra tools

# ...此外还需要配置数据库

# 执行公开网页爬虫
uv run scrapy crawl public
```

如果上次中断后重跑发现“没有新页面进入队列”，通常是因为默认去重器会加载数据库中已抓取 URL。  
可先执行一次“重新发现页面”的模式：

```shell
uv run scrapy crawl public -s KITE_DUPEFILTER_LOAD_EXISTING_URLS=0
```

说明：

- `KITE_DUPEFILTER_LOAD_EXISTING_URLS=0`：本次运行不加载数据库历史 URL，只保留本轮内去重。
- 页面/附件入库仍走 `ON CONFLICT ... DO UPDATE`，不会因为重复 URL 直接插入脏数据。

如果你希望中断后继续上一次任务（而不是从入口页重新发现），建议固定 `JOBDIR`：

```shell
uv run scrapy crawl public -s JOBDIR=.scrapy/jobs/public
```

之后即使手动停止，也可以用同一命令继续。

### 修改

如果你想针对其他网站抓取，你可能要修改 `public.py` - `PublicPageSpider` 中的 `starts_urls`，以及其 `parse` 函数中这样一段代码：

```python
if host != 'sit.edu.cn' and not host.endswith('.sit.edu.cn'):
    continue
```

祝你好运！

## Q & A

1. Windows 下无法使用 `pip` 直接安装 `Twisted` 库怎么办？  
   可以去 Pypi 网站上 [下载](https://pypi.org/project/Twisted/#files) 一个编译好的包安装。

## FreeBSD 下安装指南

1. `lxml` 库安装报错 `Please make sure the libxml2 and libxslt development packages are installed.`

   可以使用 `pkg` 安装这两个包，再 `pip install lxml` 即可。


2. `psycopg` 安装报错: `pg_config executable not found.`

   使用 `pkg` 安装 `postgresql13-client`。项目使用 `psycopg` 3.x，建议在虚拟环境中安装最新稳定版。

    ```shell
    sudo pkg install postgresql13-client
    pip install psycopg
    ```
   （小技巧：使用 `pkg search` 可以搜索相关的包。如，等到 FreeBSD 普遍使用 python38, python39 时，这些包名也会相应改变。）

3. `cryptography` 安装报错: `can't find Rust compiler`。

   这是因为一个 OpenSSL 相关的库依赖了 `cryptography` 库。 这里尝试使用 `pkg` 安装：
   ```shell
   sudo pkg install py37-cryptography (划掉
   ```
   但是会带来问题：全局环境中安装的包，和虚拟环境中安装的，并不互通。也就是说，使用 `pkg` 安装后，虚拟环境中不存在对应包。 这时候，要么放弃虚拟环境，要么安装 Rust 编译环境。其实 Rust 编译环境也很好装：

   ```shell
   sudo pkg install rust
   ```

   pkg 源中的 rust 版本总体还是蛮新的，可能会晚一个版本。相比 linux 下 apt 源更新的速度好多了。 现在再用 `pip` 安装即可。

4. 运行时报错

   ```shell
   2021-04-06 16:23:33 [twisted] CRITICAL:
   Traceback (most recent call last):
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/twisted/internet/defer.py", line 1445, in _inlineCallbacks
   result = current_context.run(g.send, result)
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/scrapy/crawler.py", line 87, in crawl
   self.engine = self._create_engine()
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/scrapy/crawler.py", line 101, in _create_engine
   return ExecutionEngine(self, lambda _: self.stop())
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/scrapy/core/engine.py", line 67, in __init__
   self.scheduler_cls = load_object(self.settings['SCHEDULER'])
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/scrapy/utils/misc.py", line 62, in load_object
   mod = import_module(module)
   File "/usr/local/lib/python3.7/importlib/__init__.py", line 127, in import_module
   return _bootstrap._gcd_import(name[level:], package, level)
   File "<frozen importlib._bootstrap>", line 1006, in _gcd_import
   File "<frozen importlib._bootstrap>", line 983, in _find_and_load
   File "<frozen importlib._bootstrap>", line 967, in _find_and_load_unlocked
   File "<frozen importlib._bootstrap>", line 677, in _load_unlocked
   File "<frozen importlib._bootstrap_external>", line 728, in exec_module
   File "<frozen importlib._bootstrap>", line 219, in _call_with_frames_removed
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/scrapy/core/scheduler.py", line 7, in <module>
   from queuelib import PriorityQueue
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/queuelib/__init__.py", line 1, in <module>
   from queuelib.queue import FifoDiskQueue, LifoDiskQueue
   File "/home/sunnysab/kite-string/venv/lib/python3.7/site-packages/queuelib/queue.py", line 5, in <module>
   import sqlite3
   File "/usr/local/lib/python3.7/sqlite3/__init__.py", line 23, in <module>
   from sqlite3.dbapi2 import *
   File "/usr/local/lib/python3.7/sqlite3/dbapi2.py", line 27, in <module>
   from _sqlite3 import *
   ModuleNotFoundError: No module named '_sqlite3'
   ```

观察到出错的 `sqlite3` 位于 `/usr/local/lib/python3.7/sqlite3` 下，可以使用 `pkg` 重装 `sqlite3`
模块。执行 `sudo pkg install py37-sqlite3-3.7.10_7
` （视实际情况定）即可解决。

## 关于作者

- 19级 化工 [@OneofFive-ops](https://github.com/OneofFive-ops)   
  项目各模块的奠基人 :D
- 18级 计算机 [@sunnysab](https://sunnysab.cn)  
  项目重构、维护，数据库和分词的对接
- 18级 计算机 [@Wanfengcxz](https://github.com/wanfengcxz)  
  PDF 文件解析

## 开源协议

项目代码基于 GPL v3 协议授权，[协议全文](LICENSE) 
