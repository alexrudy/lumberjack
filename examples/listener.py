#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from lumberjack.listener import main

if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))