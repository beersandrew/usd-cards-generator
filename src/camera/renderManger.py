#!/usr/bin/env python3

import subprocess
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def take_snapshots(cards):
    Path("renders").mkdir(parents=True, exist_ok=True)
    images = []
    renderer = get_renderer()

    def task(card):
        image_name = os.path.join("renders", card.name + ".#.png").replace("\\", "/")
        cmd = ['usdrecord', '--frames', '0:0', '--camera', card.name, '--imageWidth', '2048', '--renderer', renderer, 'cameras.usda', image_name]
        run_os_specific_usdrecord(cmd)
        return image_name.replace(".#.", ".0.")
    
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(task, cards))
    
    os.remove("cameras.usda")
    return images

def get_renderer():
    if os.name == 'nt':
        print("windows default renderer GL being used...")
        return "GL"
    else:
        if sys.platform == 'darwin':
            print("macOS default renderer Metal being used...")
            return 'Metal'
        else:
            print("linux default renderer GL being used...")
            return 'GL'

def run_os_specific_usdrecord(cmd):
    if os.name == 'nt':
        subprocess.run(cmd, check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    else:
        if sys.platform == 'darwin':
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def create_image_filename(input_path):
    return input_path.split('.')[0] + ".#.png"