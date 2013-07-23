#!/usr/bin/env python
import os
import os.path
import sys
import re
import getopt


class Log:
    def __init__(self, log_filename=None):

        self.log_filename = log_filename
        
    def process_log(self):
        if not self.log_filename:
            raise Exception, 'log_filename'
        
        fp = open(self.log_filename, "r")
        print 'Open ', self.log_filename
        buffer = {}
        impress = '/adshow.fcgi?'
        processed_records = 0
        impression = 0.0
        for line in  fp.readlines():
            if re.search(impress, line.split()[6]):
                key = line.split()[0]
                buffer[key] = buffer.get(key, 0) + 1
                impression += 1
            processed_records += 1
        print 'IP', len(buffer)
        print 'ALL IP', processed_records
        print 'ALL Impression', impression
        print 'Unic', (len(buffer) / impression) * 100




#
#################################################
#
def usage():
    print
    print "Usage:"
    print sys.argv[0] + " [logfile1] [logfile2] [logfileN]"
    print
    sys.exit(0)


if __name__ == '__main__':    
    log_filenames = []

    args = sys.argv[1:]
    try:
        (opts, getopts) = getopt.getopt(args, 'd:f:c:?hV', ["file="])
    except:
        print "\nInvalid command line option detected."
        usage()

    for opt, arg in opts:
        if opt in ('-h', '-?', '--help'):
            usage()
        if opt in ('-f', '--file'):
            print """"""
            log_filenames.append(arg)

    filenames = getopts or log_filenames

    
    if not filenames:
        print ">> You must specify atleast 1 filename to parse"
        sys.exit(1)
        

    for filename in filenames:
        print ">> Parsing log:", filename
        log = Log(filename)
        log.process_log()
