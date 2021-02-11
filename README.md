# kite-string 校园网全站爬虫

本项目是一个基于 Scrapy 框架下的爬虫脚本，旨在抓取校园网各页面，并索引进数据库。

该项目作为 [上应小风筝](https://github.com/SIT-Yiban/kite-microapp) 的一部分发布。爬虫将缓存站点网页内容和一些小一点的附件，以供后续为用户提供校园网内的文件、网页检索服务。

项目的两名作者曾经有过一些 Python 语言的经验，但是均为第一次接触 Scrapy 框架。 同时，与网上流行的针对特定条目、字段进行爬取的示例不同，本项目作为一个通用的爬虫脚本， 因而作者在探索优雅地基于 Scrapy
框架编写整站爬虫过程中，踩过不少坑。 限于精力，当前版本的项目，存在一定的效率问题，（可能）将在今后不断地改善。

该项目为 [上海应用技术大学-网站](https://www.sit.edu.cn/) 设计，不保证对其他站点有效。

**当前版本请勿用于生产环境！**
It's not ready for production environments.

## 开发环境

主要开发工具（或语言、库等）版本如下：

- Windows 10
- Ubuntu 20.04 LTS
- Python 3.9.1
- Scrapy 2.4.1
- PyCharm 2020.3

数据库正在选型。

## 运行方式

运行 kite 目录下 `run.py`

## 关于作者

- 19级 @OneofFive-ops
- 18级 @sunnysab

## 开源协议

仅供学习和交流使用