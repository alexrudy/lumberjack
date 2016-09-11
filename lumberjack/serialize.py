# -*- coding: utf-8 -*-
"""
Lumberjack utilities for serializing log records.
"""

from six.moves import cPickle as pickle
import logging
import struct
import json
import functools

class SerializingFormatter(logging.Formatter, object):
    """A base class for serializing formatters."""
    
    serializer = lambda d : d
    deserializer = logging.makeLogRecord
    
    def format(self, record):
        """Format a record, carefully handling exc_info."""
        ei = record.exc_info
        if ei:
            dummy = super(SerializingFormatter, self).format(record) # just to get traceback text into record.exc_text
            record.exc_info = None  # to avoid Unpickleable error
        s = self.serializer(record.__dict__)
        if ei:
            record.exc_info = ei  # for next handler
        return s
        
    @classmethod
    def deserialize(cls, data):
        """Deserialize data."""
        return cls.deserializer(data)

class PickleFormatter(SerializingFormatter):
    """A logging formatter that generates Pickled messages for transmission."""
    
    def serializer(self, record):
        """Serialize the record."""
        return pickle.dumps(record)
    
    @classmethod
    def deserializer(cls, s):
        """docstring for deserializer"""
        return logging.makeLogRecord(pickle.loads(s))
    
    def format(self, record):
        """
        Pickles the record in binary format with a length prefix, and
        returns it ready for transmission across the socket.
        """
        s = super(PickleFormatter, self).format(record)
        slen = struct.pack(">L", len(s))
        return slen + s
        

class JSONFormatter(SerializingFormatter):
    """Format an entire logrecord in JSON, suitable for transmission over a simple wire."""
    
    serializer = functools.partial(json.dumps, skipkeys=True)
    
    @classmethod
    def deserializer(cls, s):
        """docstring for deserializer"""
        return logging.makeLogRecord(json.loads(s))

serializers = {
    'json' : JSONFormatter,
    'pickle' : PickleFormatter,
}
