#!/usr/bin/python3
#coding: utf-8
#

import argparse
from common import *
from importlib import import_module
import traceback

def scrapy(args):
    log.debug("scrapy {}".format(args.scrapy))
    if args.scrapy:
        try:
            m = import_module('.'.join(['scrapy', args.scrapy]))
            if m and m.scrapy:
                m.scrapy(args)
        except:
            traceback.print_exc()
            pass

def main():
    command = {
        'scrapy' : scrapy
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--command', dest='command', action='store')
    parser.add_argument('-s', '--scrapy', dest='scrapy', action='store')
    parser.add_argument('-f', '--full', dest='full', action='store_true')
    parser.add_argument('-n', '--new', dest='new', action='store_true')
    parser.add_argument('-y', '--year', dest='year', action='store')
    parser.add_argument('-w', '--week', dest='week', action='store')
    args = parser.parse_args()

    log.debug("{}, {}".format(args.command, args.scrapy))

    if args.command and args.command in command:
        command[args.command](args)

if __name__ == '__main__':
    main()
