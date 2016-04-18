# -*- coding: utf-8 -*-

import logging

class NullHandler(logging.Handler):
    """Null handler does nothing."""
    
    def handle(self, record):
        pass
        
    def emit(self, record):
        pass
        
    def createLock(self):
        self.lock = None
    