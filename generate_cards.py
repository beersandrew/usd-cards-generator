#!/usr/bin/env python3

from pxr import Usd, UsdGeom, Gf, UsdUtils
import subprocess
import math
import os
import sys
import argparse
from pathlib import Path
from collections import namedtuple

Card = namedtuple('Card', ['name', 'horizontalIndex', 'verticalIndex', 'sign', 'rotations', 'translationIndex'])
Rotation = namedtuple('Rotation', ['index', 'amount'])

cards = [
    Card('XPos', 2, 1, 1, [Rotation(0, 90), Rotation(1, 90)], 0),
    Card('XNeg', 2, 1, -1, [Rotation(0, 270), Rotation(1, 270)], 0),
    Card('YPos', 2, 0, 1, [Rotation(1, 180), Rotation(0, 270)], 1),
    Card('YNeg', 2, 0, -1, [Rotation(1, 180), Rotation(0, 90)], 1),
    Card('ZPos', 0, 1, 1, [], 2),
    Card('ZNeg', 0, 1, -1, [Rotation(1, 180)], 2)
]

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
    return parser.parse_args()

def apply_cards_defaults(subject_stage, verbose):
    if verbose: 
        print("Step 1: Applying cards default values...")
    
    subject_root_prim = subject_stage.GetDefaultPrim()
    geom_model_api = UsdGeom.ModelAPI(subject_root_prim)
    geom_model_api.CreateModelApplyDrawModeAttr(False)
    geom_model_api.CreateModelCardGeometryAttr("box")
    geom_model_api.CreateModelDrawModeAttr("cards")
    geom_model_api.CreateModelDrawModeColorAttr((1, 0, 0))

    subject_stage.GetRootLayer().Save()

def generate_cards(usd_file, subject_stage, verbose):
    if verbose: 
        print("Step 2: Setting up the cameras...")

    setup_cameras(subject_stage, usd_file)
    
    if verbose:
        print("Step 3: Taking the snapshots...")
    image_names = take_snapshots()

    return image_names

def setup_cameras(subject_stage, usd_file):
    camera_stage = create_camera_stage()
    create_camera_prims(camera_stage)
    move_cameras(camera_stage, subject_stage)
    sublayer_subject(camera_stage, usd_file)

def create_camera_stage():
    stage = Usd.Stage.CreateNew('cameras.usda')
    stage.SetMetadata('metersPerUnit', 0.01)

    return stage

def create_camera_prims(camera_stage):
    for card in cards:
        camera = UsdGeom.Camera.Define(camera_stage, '/CardGenerator/' + card.name)
        camera.CreateFocalLengthAttr(50)
        camera.CreateFocusDistanceAttr(168.60936)
        camera.CreateFStopAttr(0)
        camera.CreateHorizontalApertureOffsetAttr(0)
        camera.CreateProjectionAttr("perspective")
        camera.CreateVerticalApertureOffsetAttr(0)


def move_cameras(camera_stage, subject_stage):
    for card in cards:
        camera_prim = UsdGeom.Camera.Get(camera_stage, '/CardGenerator/' + card.name)
        camera_translation = create_camera_translation(subject_stage, camera_prim, card)

        apply_camera_translation(camera_stage, camera_prim, camera_translation)

        for rotation in card.rotations:
            apply_camera_rotation(camera_stage, camera_prim, rotation.index, rotation.amount)
        
def create_camera_translation(subject_stage, camera_prim, card):
    bounding_box = get_bounding_box(subject_stage)
    min_bound = bounding_box.GetMin()
    max_bound = bounding_box.GetMax()

    subject_center = (min_bound + max_bound) / 2.0

    bounding_box_width = (max_bound[card.horizontalIndex] - min_bound[card.horizontalIndex]) * 10
    bounding_box_height = (max_bound[card.verticalIndex] - min_bound[card.verticalIndex]) * 10
    focal_length = camera_prim.GetFocalLengthAttr().Get()

    distance = get_distance_to_camera(bounding_box_width, bounding_box_height, focal_length)
    distance *= card.sign

    flip_aperatures = False
    for rotation in card.rotations:
        if rotation.amount != 180:
            flip_aperatures = True
            break
    
    actual_horizontal_aperture = focal_length * bounding_box_width / distance
    actual_vertical_aperture = focal_length * bounding_box_height / distance

    if flip_aperatures:
        camera_prim.CreateHorizontalApertureAttr(actual_vertical_aperture)
        camera_prim.CreateVerticalApertureAttr(actual_horizontal_aperture)
    else:
        camera_prim.CreateHorizontalApertureAttr(actual_horizontal_aperture)
        camera_prim.CreateVerticalApertureAttr(actual_vertical_aperture)


    return subject_center + get_camera_translation(distance, card.translationIndex)

def get_bounding_box(subject_stage):
    bboxCache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    # Compute the bounding box for all geometry under the root
    root = subject_stage.GetPseudoRoot()
    return bboxCache.ComputeWorldBound(root).GetBox()

def get_distance_to_camera(bounding_box_width, bounding_box_height, focal_length):
    distance_to_capture_horizontal = calculate_field_of_view_distance(24, bounding_box_width, focal_length)
    distance_to_capture_vertical = calculate_field_of_view_distance(24, bounding_box_height, focal_length)

    max_distance = max(distance_to_capture_horizontal, distance_to_capture_vertical)

    return max_distance

def calculate_field_of_view_distance(sensor_size, object_size, focal_length):
    return calculate_camera_distance(object_size, calculate_field_of_view(focal_length, sensor_size))
    
def calculate_field_of_view(focal_length, sensor_size):
    # Focal length and sensor size should be in the same units (e.g., mm)
    field_of_view = 2 * math.atan(sensor_size / (2 * focal_length))
    return field_of_view

def calculate_camera_distance(subject_size, field_of_view):
    # Subject size and field of view should be in the same units (e.g., mm and degrees)
    distance = (subject_size / 2) / math.tan(field_of_view / 2)
    return distance

def get_camera_translation(distance, translationIndex):
    vector = Gf.Vec3d(0, 0, 0)
    vector[translationIndex] = distance / 10.0 # convert units from mm to cm
    return vector

def apply_camera_translation(camera_stage, camera_prim, camera_translation):
    xformRoot = UsdGeom.Xformable(camera_prim.GetPrim())
    translateOp = xformRoot.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble)
    translateOp.Set(camera_translation)
    camera_stage.Save()

def apply_camera_rotation(camera_stage, camera_prim, rotationDirection, rotationAmount):
    xformRoot = UsdGeom.Xformable(camera_prim.GetPrim())
    if rotationDirection == 0:
        rotateOp = xformRoot.AddRotateXOp()
        rotateOp.Set(rotationAmount)
    elif rotationDirection == 1:
        rotateOp = xformRoot.AddRotateYOp()
        rotateOp.Set(rotationAmount)
    else:
        rotateOp = xformRoot.AddRotateZOp()
        rotateOp.Set(rotationAmount)

    camera_stage.Save()

def sublayer_subject(camera_stage, input_file):
    camera_stage.GetRootLayer().subLayerPaths = [input_file]
    camera_stage.GetRootLayer().Save()

def take_snapshots():
    Path("renders").mkdir(parents=True, exist_ok=True)
    images = []
    renderer = get_renderer()
    for card in cards:
        image_name = os.path.join("renders", card.name + ".#.png").replace("\\", "/")
        cmd = ['usdrecord', '--frames', '0:0', '--camera', card.name, '--imageWidth', '2048', '--renderer', renderer, 'cameras.usda', image_name]
        run_os_specific_usdrecord(cmd)
        images.append(image_name.replace(".#.", ".0."))
    
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

def link_images_to_subject(subject_stage, images):
    subject_root_prim = subject_stage.GetDefaultPrim()
    subject_root_prim.SetMetadata("kind", "component")
    geom_model_api = UsdGeom.ModelAPI(subject_root_prim)

    geom_model_api.CreateModelCardTextureXPosAttr(images[0])
    geom_model_api.CreateModelCardTextureXNegAttr(images[1])
    geom_model_api.CreateModelCardTextureYPosAttr(images[2])
    geom_model_api.CreateModelCardTextureYNegAttr(images[3])
    geom_model_api.CreateModelCardTextureZPosAttr(images[4])
    geom_model_api.CreateModelCardTextureZNegAttr(images[5])
    geom_model_api.CreateModelApplyDrawModeAttr(True)

    subject_stage.GetRootLayer().Save()
    
def create_usdz_wrapper_stage(usdz_file, usdz_wrapper_name):
    existing_stage = Usd.Stage.Open(usdz_file)
    new_stage = Usd.Stage.CreateNew(usdz_wrapper_name)
    
    UsdUtils.CopyLayerMetadata(existing_stage.GetRootLayer(), new_stage.GetRootLayer())

    new_stage.GetRootLayer().subLayerPaths = [usdz_file]
    new_stage.GetRootLayer().Save()
    return new_stage

def zip_results(usd_file, images, is_usdz, usdz_wrapper_name):
    file_list = [usd_file] + images

    if is_usdz:
        file_list.append(usdz_wrapper_name)
        
    usdz_file = usd_file.split('.')[0] + '_Cards.usdz'
    cmd = ["usdzip", "-r", usdz_file] + file_list
    subprocess.run(cmd)

if __name__ == "__main__":

    args = parse_args()

    usd_file = args.usd_file
    is_usdz = ".usdz" in usd_file
    usdz_wrapper_name = usd_file.split('.')[0] + '_Cards.usda'

    subject_stage = create_usdz_wrapper_stage(usd_file, usdz_wrapper_name) if is_usdz else Usd.Stage.Open(usd_file)

    apply_cards_defaults(subject_stage, args.verbose)

    file_to_sublayer = usdz_wrapper_name if is_usdz else usd_file
        
    images = generate_cards(file_to_sublayer, subject_stage, args.verbose)

    if args.verbose:
        print("Step 4: Linking cards to subject...")

    link_images_to_subject(subject_stage, images)

    if args.create_usdz_result:
        if args.verbose:
            print("Step 5: Zipping cards as usdz...")
        
        zip_results(usd_file, images, is_usdz)