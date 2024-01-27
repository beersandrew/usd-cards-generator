#!/usr/bin/env python3

import argparse
from collections import namedtuple

Args = namedtuple('Args', ['usd_file', 'create_usdz_result', 'verbose', 'is_usdz', 'usdz_wrapper_name', 'file_to_sublayer', 'output_extension', 'dome_light', 'apply_cards', 'render_purposes', 'image_width'])

def parse_args():
    parser = argparse.ArgumentParser(description="This script generates cards for a given USD file and associates them with the file.")
    parser.add_argument('usd_file', 
                        type=str, 
                        help='The USD file you want to add cards to. If USDZ is input, a new USD file will be created to wrap the existing one called <input>_Cards.usd')
    parser.add_argument('--dome-light',
                        type=str,
                        help='The path to the dome light HDR image to use, if any')
    parser.add_argument('--create-usdz-result', 
                        action='store_true',
                        help='Returns the resulting files as a new usdz file called <input>_Cards.usdz')
    parser.add_argument('--output-extension', 
                    type=str, 
                    help='The file extension of the output image you want (exr, png..). If using exr, make sure your usd install includes OpenEXR',
                    default='png')
    parser.add_argument('--verbose', 
                        action='store_true',
                        help='Prints out the steps as they happen')
    parser.add_argument('--apply-cards', 
                        action='store_true',
                        help='Saves the images as the cards for the given USD file.')
    parser.add_argument('--render-purposes', 
                        type=str,
                        help='A comma separated list of render purposes to include in the thumbnail. Valid values are: default, render, proxy, guide.',
                        default='default')
    parser.add_argument('--image-width',
                        type=int,
                        help='The width of the image to generate. Default is 2048.',
                        default=2048)
    
    args = parser.parse_args()

    is_usdz = ".usdz" in args.usd_file
    usdz_wrapper_name = args.usd_file.split('.')[0] + '_Cards.usda'
    file_to_sublayer = usdz_wrapper_name if is_usdz else args.usd_file

    return Args(args.usd_file, 
                args.create_usdz_result, 
                args.verbose, 
                is_usdz, 
                usdz_wrapper_name, 
                file_to_sublayer,
                args.output_extension,
                args.dome_light,
                args.apply_cards,
                args.render_purposes,
                args.image_width)

