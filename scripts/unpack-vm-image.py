#!/usr/bin/env python3
"""Unpack one gzip member; OpenWrt may append fwtool metadata after it."""
from pathlib import Path
import sys,zlib

def unpack(source,destination):
    decoder=zlib.decompressobj(31)
    with Path(source).open('rb') as src,Path(destination).open('wb') as dst:
        while not decoder.eof:
            block=src.read(1024*1024)
            if not block: raise ValueError('Truncated gzip image')
            dst.write(decoder.decompress(block))
        dst.write(decoder.flush())

if __name__=='__main__':
    unpack(sys.argv[1],sys.argv[2])
