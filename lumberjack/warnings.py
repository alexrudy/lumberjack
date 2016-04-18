# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import warnings

def showwarning_lumberjack(message, category, filename, lineno, line=None, file=None):
    """Adjust warnings formatting."""
    logging.getLogger("py.warnings").warning("{0} [{1}]".format(message, category.__name__), extra={'category':category.__name__})
    
_showwarning_original = None
def captureWarnings(capture=False):
    """Set up the warnings logger"""
    global _showwarning_original
    if capture:
        if _showwarning_original is None:
            warnings_logger = logging.getLogger("py.warnings")
            if not warnings_logger.handlers and hasattr(logging, 'NullHandler'):
                warnings_logger.addHandler(logging.NullHandler())
            _showwarning_original = warnings.showwarning
            warnings.showwarning = showwarning_lumberjack
    else:
        if _showwarning_original is not None:
            warnings.showwarning = _showwarning_original
            _showwarning_original = None
