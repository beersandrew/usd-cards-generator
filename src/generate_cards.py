#!/usr/bin/env python3

from pxr import Usd, UsdGeom, UsdUtils
import subprocess

from collections import namedtuple
from camera.cameraManager import setup_cameras
from camera.renderManger import take_snapshots
from utils.arg_parser import parse_args

Card = namedtuple('Card', ['name', 'horizontalIndex', 'verticalIndex', 'sign', 'rotations', 'translationIndex'])
Rotation = namedtuple('Rotation', ['index', 'amount'])

cards = [
    Card('XPos', 2, 1, 1, [Rotation(0, 90), Rotation(1, 90)], 0),
    Card('XNeg', 2, 1, -1, [Rotation(0, 90), Rotation(1, 270)], 0),
    Card('YPos', 2, 0, 1, [Rotation(1, 180), Rotation(0, 270)], 1),
    Card('YNeg', 2, 0, -1, [Rotation(0, 90)], 1),
    Card('ZPos', 0, 1, 1, [], 2),
    Card('ZNeg', 0, 1, -1, [Rotation(2, 180), Rotation(1, 180)], 2)
]

def generate_card_images(usd_file, subject_stage, dome_light, output_extension, verbose, apply_cards, render_purposes):

    if apply_cards:
        if verbose: 
            print("Step 1: Applying cards default values...")
        apply_cards_defaults(subject_stage, verbose)

    if verbose: 
        print("Step 2: Setting up the cameras...")

    setup_cameras(subject_stage, usd_file, cards, dome_light, render_purposes)
    
    if verbose:
        print("Step 3: Taking the snapshots...")

    image_names = take_snapshots(cards, output_extension)

    return image_names

def apply_cards_defaults(subject_stage, verbose):
    subject_root_prim = subject_stage.GetDefaultPrim()
    subject_root_prim.SetMetadata("kind", "component")
    UsdGeom.ModelAPI.Apply(subject_root_prim)
    geom_model_api = UsdGeom.ModelAPI(subject_root_prim)
    geom_model_api.CreateModelApplyDrawModeAttr(False)
    geom_model_api.CreateModelCardGeometryAttr("box")
    geom_model_api.CreateModelDrawModeAttr("cards")
    geom_model_api.CreateModelDrawModeColorAttr((1, 0, 0))

def link_images_to_subject(subject_stage, images):
    subject_root_prim = subject_stage.GetDefaultPrim()
    
    geom_model_api = UsdGeom.ModelAPI(subject_root_prim)
    geom_model_api.CreateModelCardTextureXPosAttr(images[0])
    geom_model_api.CreateModelCardTextureXNegAttr(images[1])
    geom_model_api.CreateModelCardTextureYPosAttr(images[2])
    geom_model_api.CreateModelCardTextureYNegAttr(images[3])
    geom_model_api.CreateModelCardTextureZPosAttr(images[4])
    geom_model_api.CreateModelCardTextureZNegAttr(images[5])
    geom_model_api.CreateModelApplyDrawModeAttr(True)
    
def create_usdz_wrapper_stage(usdz_file, usdz_wrapper_name):
    existing_stage = Usd.Stage.Open(usdz_file)
    new_stage = Usd.Stage.CreateNew(usdz_wrapper_name)
    
    UsdUtils.CopyLayerMetadata(existing_stage.GetRootLayer(), new_stage.GetRootLayer())

    new_stage.GetRootLayer().subLayerPaths = [usdz_file]
    
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

    subject_stage = create_usdz_wrapper_stage(args.usd_file, args.usdz_wrapper_name) if args.is_usdz else Usd.Stage.Open(args.usd_file)

    images = generate_card_images(args.file_to_sublayer, subject_stage, args.dome_light, args.output_extension, args.verbose, args.apply_cards, args.render_purposes)

    if args.apply_cards:
        if args.verbose:
            print("Step 4: Linking cards to subject...")
        link_images_to_subject(subject_stage, images)

    subject_stage.GetRootLayer().Save()

    if args.create_usdz_result:
        if args.verbose:
            print("Step 5: Zipping cards as usdz...")
        
        zip_results(args.usd_file, images, args.is_usdz)