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

DEFAULT_APP = "pygeoapi_provider"
"""
Used for datacube object initialization to trigger datacube.conf find feature
"""

BBOX_COORD_PRECISION = "{:.4f}"
"""
Format string for BoundBox coordinates. Limits float output to four decimal places
"""

CACHE_PICKLE = 'ogc-tb-17/DATA/odc_cache.pickle'
"""
Path to ODC cache pickle file

Defaults to /ogc-tb-17/DATA/odc_cache.pickle
"""