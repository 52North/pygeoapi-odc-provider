# =================================================================
# Copyright (C) 2021-2021 52°North Spatial Information Research GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#    http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =================================================================
from datacube.utils.geometry import BoundingBox
from pyproj import Transformer

from .constants import BBOX_COORD_PRECISION


def convert_datacube_bbox_to_wgs84(bbox: BoundingBox, in_crs: str = 'epsg:4326', always_xy: bool = True) -> BoundingBox:
    """
    Converts the given bbox coordinates from source to wgs84
    :param bbox: datacube.utils.geometry._base.BoundingBox
    :param in_crs:
    :param always_xy:
    :returns bbox: datacube.utils.geometry._base.BoundingBox
    """
    out_crs = 'epsg:4326'
    if in_crs == out_crs:
        return bbox

    # Without always_xy=True the transform function would return (lat, long)
    transformer = Transformer.from_crs(in_crs, out_crs, always_xy=always_xy)
    left_wgs84, bottom_wgs84 = transformer.transform(bbox.left, bbox.bottom)
    right_wgs84, top_wgs84 = transformer.transform(bbox.right, bbox.top)

    return BoundingBox.from_points((left_wgs84, bottom_wgs84), (right_wgs84, top_wgs84))


def convert_datacube_bbox_to_geojson_wgs84_polygon(bbox: BoundingBox, in_crs: str ='epsg:4326', always_xy: bool = True) -> [[[]]]:
    """
    Converts the given bbox coordinates from source to wgs84
    :param bbox: datacube.utils.geometry._base.BoundingBox
    :param in_crs:
    :param always_xy:
    :returns wgs84 polygon in the format [[[ul], [ur], [lr], [ll], [ul]]]
    """

    left_wgs84, bottom_wgs84, right_wgs84, top_wgs84 = convert_datacube_bbox_to_wgs84(bbox, in_crs, always_xy)

    #
    # Required coordinates for polygon: ul, ur, lr, ll, ul
    #
    return [[
        [top_wgs84,    left_wgs84],   # ul
        [top_wgs84,    right_wgs84],  # ur
        [bottom_wgs84, right_wgs84],  # lr
        [bottom_wgs84, left_wgs84],   # ll
        [top_wgs84,    left_wgs84]    # ul
    ]]


def apply_precision(coord: float) -> float:
    return float(BBOX_COORD_PRECISION.format(coord))
