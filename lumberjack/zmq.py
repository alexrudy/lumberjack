# -*- coding: utf-8 -*-
"""
Helpers for serializing over ZMQ
"""

from __future__ import print_function, absolute_import

import sys
import six
import logging
import threading
import collections

from six.moves.urllib.parse import urlparse, parse_qs, urlunparse

from .serialize import serializers

try:
    import zmq
except ImportError as e:
    print("The python bindings for ZMQ are required to use lumberjack.zmq\nPlease install pyzmq.", file=sys.stderr)

class ZMQPublisher(logging.Handler, object):
    """A handler which publishes log messages to a ZMQ socket.
    
    The logger name is used as the topic selector for publishing.
    """
    def __init__(self, interface_or_socket, context=None, bind=False):
        super(ZMQPublisher, self).__init__()
        if isinstance(interface_or_socket, zmq.Socket):
            self.socket = interface_or_socket
            self.ctx = self.socket.context
        else:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.PUB)
            if bind:
                self.socket.bind(interface_or_socket)
            else:
                self.socket.connect(interface_or_socket)
        
    def emit(self, record):
        """Emit a record over the ZMQ socket."""
        try:
            msg = self.format(record)
            self.socket.send_multipart([record.name, msg])
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
            
        
    def close(self):
        """Close the ZMQ publisher."""
        self.socket.close()
        
    

class ZMQLogWatcher(threading.Thread, object):
    """A ZMQ Log watcher. Can be run independently, or in a thread."""
    
    @classmethod
    def from_url(cls, url):
        """Make a log watcher with a URL."""
        
        # Get the options out of the URL.
        result = urlparse(url)
        options = parse_qs(result.query)
        channel = options.get("channel", "")
        serializer = serializers[options.get("serialize", "json")]
        
        # Rebuild the URL without the query string.
        args = list(result)
        args[4] = ''
        url = urlunparse(args)
        
        # Set up the object.
        obj = cls(url, channel, serializer.deserialize)
        obj.subscribe(channel)
        return obj
    
    def __init__(self, interface_or_socket, context=None, deserialize="json"):
        super(ZMQLogWatcher, self).__init__()
        if isinstance(interface_or_socket, zmq.Socket):
            self.socket = interface_or_socket
            self.ctx = self.socket.context
        else:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.SUB)
            self.socket.connect(interface_or_socket)
        
        if deserialize is None:
            self.deserialize = logging.makeLogRecord
        elif isinstance(deserialize, six.string_types):
            self.deserialize = serializers[deserialize].deserialize
        else:
            self.deserialize = deserialize
        
        self._sockopts = collections.deque()
        
        self._shouldrun = threading.Event()
        
        self._signal_address = "inproc://signal-{0}".format(hex(id(self)))
        self._signal_socket = self.ctx.socket(zmq.PULL)
        self._signal_socket.connect(self._signal_address)
        
        # Set up polling for interrupts.
        self._poller = zmq.Poller()
        self._poller.register(self.socket, zmq.POLLIN)
        self._poller.register(self._signal_socket, zmq.POLLIN)
    
    def stop(self):
        """Stop this thread."""
        if not self.isAlive():
            return
        if not self._shouldrun.isSet():
            return
        
        self._shouldrun.clear()
        self._send_signal()
        return
    
    def _send_signal(self):
        """Send a signal to the thread."""
        signal = self.ctx.socket(zmq.PUSH)
        signal.connect(self._signal_address)
        signal.send(b"")
        signal.close()
        
    def __del__(self):
        """When destroyed, close the signaler."""
        self._signal_socket.close()
    
    def start(self):
        """Start the thread."""
        self._shouldrun.set()
        super(ZMQLogWatcher, self).start()
    
    def subscribe(self, name):
        """Subscribe to a channel."""
        self.setsockopt(zmq.SUBSCRIBE, name)
    
    def setsockopt(self, key, name):
        """Set a sockopt in a threadsafe way."""
        self._sockopts.append((key, name))
        self._send_signal()
        
    def _adjust_sockopts(self):
        """Multithreaded subscription."""
        while len(self._sockopts):
            (key, name) = self._sockopts.popleft()
            self.socket.setsockopt(key, name)
        
    def run(self):
        """Run the log watcher."""
        while self._shouldrun.isSet():
            self._adjust_sockopts()
            ready = dict(self._poller.poll(timeout=100))
            if self._signal_socket in ready:
                sentinel = self._signal_socket.recv()
                continue
            if self.socket in ready:
                name, msg = self.socket.recv_multipart()
                record = self.deserialize(msg)
                logging.getLogger(name).handle(record)
            
