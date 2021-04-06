# kite-string 校园网全站爬虫

本项目是一个基于 Scrapy 框架下的爬虫脚本，旨在抓取校园网各页面，并索引进数据库。

当前已实现抓取的信息：

- [x] 公开页面
- [x] 校内公告
- [ ] 图书馆

该项目作为 [上应小风筝](https://github.com/SIT-Yiban/kite-microapp) 的一部分发布。爬虫将缓存站点网页内容和一些小一点的附件，以供后续为用户提供校园网内的文件、网页检索服务。

项目的两名作者曾经有过一些 Python 语言的经验，但是均为第一次接触 Scrapy 框架。 同时，与网上流行的针对特定条目、字段进行爬取的示例不同，本项目作为一个通用的爬虫脚本， 因而作者在探索优雅地基于 Scrapy
框架编写整站爬虫过程中，踩过不少坑。 限于精力，当前版本的项目，存在一定的效率问题，（可能）将在今后不断地改善。

该项目为 [上海应用技术大学-网站](https://www.sit.edu.cn/) 设计，不保证对其他站点有效。

## 开发环境

主要开发工具（或语言、库等）版本如下：

- Windows 10
- Ubuntu 20.04 LTS
- Python 3.9.1
- Scrapy 2.4.1
- PyCharm 2020.3
- PostgreSQL 13.2
- zhparser

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

# 校内账户系统账号
OA_USER = '学号/工号'
OA_PASSWD = '密码'
```

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

如果您运行 `public` 爬虫，大部分页面是可以在公网访问到的。如果运行 `private` 爬虫，请务必保证处于校园网环境（包括使用学校 VPN 系统）。 抓取速度受网络和校方服务器限制，调高 `settings.py`
中并发所带来的收益并不大。

在并发请求数设置为 `128` 的情况下，作者最近一次运行 `public` 爬虫抓取用时约 4 小时，实际并发连接数保持在 100 左右。
`private` 爬虫运行较快，数十秒便可运行结束。

截至 README.md 文档修改时，公开网页约 12 万篇（过滤后超 5 万篇），附件近 1 万个，校内公告两千余篇。

### 执行方式

执行

```shell
git clone https://github.com/sunnysab/kite-string
cd kite-string

# 安装必要的依赖库
pip install -r requirements.txt

# ...此外还需要配置数据库

# 执行校内公告爬虫
scrapy crawl private
# 执行公开网页爬虫
scrapy crawl public
```

### 修改

如果你想针对其他网站抓取，你可能要修改 `public.py` - `PublicPageSpider` 中的 `starts_urls`，以及其 `parse` 函数中这样一段代码：

```python
if '.sit.edu.cn' not in url:
    continue
```

祝你好运！

## Q & A

1. Windows 下无法使用 pip 直接安装 Twisted 库怎么办？

可以去 Pypi 网站上 [下载](https://pypi.org/project/Twisted/#files) 一个编译好的包安装。

## 关于作者

- 19级 [@OneofFive-ops](https://github.com/OneofFive-ops)
- 18级 [@sunnysab](https://sunnysab.cn)

## 开源协议

项目代码基于 GPL v3 协议授权，[协议](LICENSE) 