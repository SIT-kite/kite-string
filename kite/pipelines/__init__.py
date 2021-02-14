# -*- coding: utf-8 -*-
# @Time    : 2021/2/11 17:14
# @Author  : sunnysab
# @File    : __init__.py

from scrapy.utils.project import get_project_settings


# attachment directory
download_directory = get_project_settings()['FILES_STORE']

# Exports
from .page import PagePipeline
from .caching import FileCachingPipeline
from .attachment import AttachmentPipeline
