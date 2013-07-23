#!/usr/bin/python
# encoding: utf-8
#This Python file uses the following encoding: utf-8
import optparse
import sys
import re 
from pprint import pprint

def filereader(filein):
    buffer = []
    fin = open(filein, 'r')
    for line in fin:
        buffer.append(line)
    return buffer
def filewriter(fileout, words):
    fout = open(fileout, 'w')
    for key, valye in words.items():
        fout.write(str(key)+'\n')

def generaator(filein, fileout):
    inline = filereader(filein)
    buffer = {}
    for item in inline:
        words_line = item.decode('utf-8').lower()
        compiled_re = re.compile('[\w]*',re.IGNORECASE|re.UNICODE)
        lines = compiled_re.findall(words_line)
        for line in lines:
            line.strip()
            if line != '':
                buffer[str(line.encode('utf-8'))] = 1
    filewriter(fileout, buffer)
def main():
    usage = 'usage: '
    description= 'Stop words generator'
    parser = optparse.OptionParser(description=description, usage=usage)
    parser.add_option('--filein', default=None, help="read file")
    parser.add_option('--fileout', default=None, help="output file")
    options, arguments = parser.parse_args()
    if options.filein and options.fileout:
        generaator(options.filein, options.fileout)
    else:
        parser.print_help()
if __name__ == '__main__':
    main()
