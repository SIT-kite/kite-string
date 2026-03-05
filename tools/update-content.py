# -*- coding: utf-8 -*-
#
# Backward-compatible launcher for the renamed module.
#
import runpy
from pathlib import Path


if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('update_content.py')), run_name='__main__')
