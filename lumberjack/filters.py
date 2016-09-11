# -*- coding: utf-8 -*-

import logging

class Filter(logging.Filter, object):
    """
    Filter instances are used to perform arbitrary filtering of LogRecords.

    Loggers and Handlers can optionally use Filter instances to filter
    records as desired. The base filter class only allows events which are
    below a certain point in the logger hierarchy. For example, a filter
    initialized with "A.B" will allow events logged by loggers "A.B",
    "A.B.C", "A.B.C.D", "A.B.D" etc. but not "A.BB", "B.A.B" etc. If
    initialized with the empty string, all events are passed.
    """
    def __init__(self, name=''):
        """
        Initialize a filter.

        Initialize with the name of the logger which, together with its
        children, will have its events allowed through the filter. If no
        name is specified, allow every event.
        """
        super(Filter, self).__init__(name)
        
    @property
    def name(self):
        """Name property"""
        return self._name
        
    @name.setter
    def name(self, name):
        """Set the name"""
        self._name = name
        self._nlen = len(name)

    def filter(self, record):
        """
        Determine if the specified record is to be logged.

        Is the specified record to be logged? Returns 0 for no, nonzero for
        yes. If deemed appropriate, the record may be modified in-place.
        """
        if self._nlen == 0:
            return 1
        elif self._name == record.name:
            return 1
        elif not record.name.startswith(self._name):
            return 0
        return (record.name[self._nlen] == ".")
