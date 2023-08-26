#!/usr/bin/env python3

import argparse
from collections import namedtuple

Args = namedtuple('Args', ['usd_file', 'create_usdz_result', 'verbose', 'is_usdz', 'usdz_wrapper_name', 'file_to_sublayer'])

def parse_args():
    parser = argparse.ArgumentParser(description="This script generates cards for a given USD file and associates them with the file.")
    parser.add_argument('usd_file', 
                        type=str, 
                        help='The USD file you want to add cards to. If USDZ is input, a new USD file will be created to wrap the existing one called <input>_Cards.usd')
    parser.add_argument('--create-usdz-result', 
                        action='store_true',
                        help='Returns the resulting files as a new usdz file called <input>_Cards.usdz')
    parser.add_argument('--verbose', 
                        action='store_true',
                        help='Prints out the steps as they happen')
    
    args = parser.parse_args()

    is_usdz = ".usdz" in args.usd_file
    usdz_wrapper_name = args.usd_file.split('.')[0] + '_Cards.usda'
    file_to_sublayer = args.usdz_wrapper_name if is_usdz else args.usd_file

    return Args(args.usd_file, args.create_usdz_result, args.verbose, is_usdz, usdz_wrapper_name, file_to_sublayer)

