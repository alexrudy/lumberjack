# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

__version__ = "0.2.1"

import logging
from .config import configure
from .warnings import captureWarnings
from .streams import ColorLevelFormatter, SplitStreamHandler, ColorStreamHandler

__all__ = ['setup_logging', 'captureWarnings', 'ColorLevelFormatter', 'SplitStreamHandler', 'ColorStreamHandler']

def setup_logging(mode='stream', increment=False, level=logging.NOTSET, warnings=True):
    """A quick way to set up logging for a particular logger."""
    logging.addLevelName(5, "MSG")
    configure(mode, disable_existing_loggers = not increment)
    logging.getLogger().setLevel(logging.NOTSET)
    captureWarnings(warnings)
