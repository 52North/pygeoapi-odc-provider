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
from odcprovider.utils import convert_datacube_bbox_to_wgs84
from datacube.utils.geometry import BoundingBox
from pytest import approx
from pyproj import CRS, Transformer


def test_convert_datacube_bbox_to_wgs84():
    # output EPSG
    # bbox = -101.5, 53.875, -101.375, 54.0
    # input: EPSG:2957
    # [730067.3869262065, 5975292.282435977, 737568.9582588983, 5989604.177507464]

    input_bbox = BoundingBox.from_points((730067.3869262065, 5975292.282435977), (737568.9582588983, 5989604.177507464))
    in_crs = 'epsg:2957'

    output_bbox = convert_datacube_bbox_to_wgs84(input_bbox, in_crs)

    epsilon = 0.000001

    assert output_bbox.bottom == approx(53.875, epsilon)
    assert output_bbox.left == approx(-101.5, epsilon)
    assert output_bbox.right == approx(-101.375, epsilon)
    assert output_bbox.top == approx(54.0, epsilon)
