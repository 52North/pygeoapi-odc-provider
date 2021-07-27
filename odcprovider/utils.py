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
from pyproj import Transformer

BBOX_COORD_PRECISION = "{:.4f}"


def convert_datacube_bbox_to_geojson_wgs84_polygon(bbox, in_crs='epsg:4326'):
    """
    Converts the given bbox coordinates from source to wgs84
    """
    out_crs = 'epsg:4326'
    if in_crs == out_crs:
        return bbox

    transformer = Transformer.from_crs(in_crs, out_crs)
    left_wgs84, top_wgs84 = transformer.transform(bbox.left, bbox.top)
    right_wgs84, bottom_wgs84 = transformer.transform(bbox.right, bbox.bottom)
    #
    # Required coordinates for polygon: ul, ur, lr, ll, ul
    #
    return [[
        [apply_precision(top_wgs84),    apply_precision(left_wgs84)],   # ul
        [apply_precision(top_wgs84),    apply_precision(right_wgs84)],  # ur
        [apply_precision(bottom_wgs84), apply_precision(right_wgs84)],  # lr
        [apply_precision(bottom_wgs84), apply_precision(left_wgs84)],   # ll
        [apply_precision(top_wgs84),    apply_precision(left_wgs84)]    # ul
    ]]


def apply_precision(coord: float) -> float:
    return float(BBOX_COORD_PRECISION.format(coord))
