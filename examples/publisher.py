#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A quick publisher to send lots of messages.
"""

import logging
import argparse
import time
import random
import zmq
import string
from lumberjack.zmq import ZMQPublisher
from lumberjack.serialize import JSONFormatter
from lumberjack.streams import ColorStreamHandler

def main():
    """Main loop function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    parser.add_argument("name", type=str)
    parser.add_argument("-f", "--frequency", type=float, default=10.0)
    opt = parser.parse_args()
    
    ctx = zmq.Context.instance()
    pub = ctx.socket(zmq.PUB)
    pub.bind(opt.url)
    
    handler = ZMQPublisher(pub)
    handler.setFormatter(JSONFormatter())
    handler.setLevel(1)
    logger = logging.getLogger(opt.name)
    logger.addHandler(handler)
    logger.setLevel(1)
    
    print("Publishing to {0}.".format(opt.url))
    print("^C to exit.")
    
    try:
        while True:
            time.sleep((random.random() / opt.frequency) + (1.0 / opt.frequency))
            level = random.choice([5]*5 + [10]*5 + [20, 20, 30, 40, 50])
            letter = random.choice(string.ascii_letters)
            logger.getChild(letter).log(level, "Message at level {0}".format(level))
    except KeyboardInterrupt:
        print("...done")

if __name__ == '__main__':
    main()
