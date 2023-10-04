#!/usr/bin/env python3

from pxr import Usd, UsdGeom, UsdLux
from collections import namedtuple
from camera.cameraGenerator import create_camera_for_card

BoundingBox = namedtuple('BoundingBox', ['width', 'height'])

def setup_cameras(subject_stage, usd_file, cards, dome_light):
    camera_stage = create_camera_stage()
    create_cameras(camera_stage, subject_stage, cards)
    sublayer_subject(camera_stage, usd_file)

    if dome_light:
        add_domelight(camera_stage, dome_light)
    
    camera_stage.Save()

def create_camera_stage():
    stage = Usd.Stage.CreateNew('cameras.usda')
    stage.SetMetadata('metersPerUnit', 0.01)

    return stage

def create_cameras(camera_stage, subject_stage, cards):
    stage_bounding_box = get_bounding_box(subject_stage)
    min_bound = stage_bounding_box.GetMin()
    max_bound = stage_bounding_box.GetMax()
    subject_center = (min_bound + max_bound) / 2.0

    for card in cards:
        card_width = (max_bound[card.horizontalIndex] - min_bound[card.horizontalIndex]) * 10
        card_height = (max_bound[card.verticalIndex] - min_bound[card.verticalIndex]) * 10
        card_bounding_box = BoundingBox(card_width, card_height)

        create_camera_for_card(card, camera_stage, subject_center, card_bounding_box)

def get_bounding_box(subject_stage):
    bboxCache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    # Compute the bounding box for all geometry under the root
    root = subject_stage.GetPseudoRoot()
    return bboxCache.ComputeWorldBound(root).GetBox()


def sublayer_subject(camera_stage, input_file):
    camera_stage.GetRootLayer().subLayerPaths = [input_file]

def add_domelight(camera_stage, dome_light):
    UsdLux.DomeLight.Define(camera_stage, '/CardGenerator/DomeLight')
    domeLight = UsdLux.DomeLight(camera_stage.GetPrimAtPath('/CardGenerator/DomeLight'))
    domeLight.CreateTextureFileAttr().Set(dome_light)
    domeLight.CreateTextureFormatAttr().Set("latlong")