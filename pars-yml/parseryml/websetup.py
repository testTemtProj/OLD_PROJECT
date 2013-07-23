"""Setup the ParserYML application"""
import logging

from parseryml.config.environment import load_environment

import os
import time
log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup parseryml here"""
    
    DIRS = ('./parseryml/other/ARHIVES', 
            './parseryml/other/hashes', 
            './parseryml/other/IMG', 
            './parseryml/other/IMG_OUT', 
            './parseryml/other/IMG_OUT/128x80', 
            './parseryml/other/IMG_OUT/213x168', 
            './parseryml/other/IMG_OUT/98x83', 
            './parseryml/other/OLD_YML',
            './parseryml/other/YML')
    
    for dir in DIRS:
        print "create folder: %s" % dir
        if not os.path.exists(dir):
            os.makedirs(dir)
    load_environment(conf.global_conf, conf.local_conf)
    
    