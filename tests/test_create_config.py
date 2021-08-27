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
import datacube.utils.geometry

from src.create_config import _merge_config,_create_resource_from_odc_product
from tempfile import NamedTemporaryFile
import yaml
import pickle


def test__merge_config():
    data = {
        'resources': {
            'test_product': {
                'test_key': 'test_value'
            }
        }
    }

    initial_data = {
        'metadata': 'metadata_value',
        'resources': {
            'initial_product': {
                'initial_key': 'initial_value'
            }
        }
    }

    infile = NamedTemporaryFile()
    with open(infile.name, 'w') as f:
        yaml.dump(initial_data, f, default_flow_style=False, sort_keys=False)

    merged_config = _merge_config(infile.name, data)
    assert 'metadata' in merged_config
    assert merged_config['metadata'] == 'metadata_value'
    assert 'resources' in merged_config
    assert 'initial_product' in merged_config['resources']
    assert 'initial_key' in merged_config['resources']['initial_product']
    assert merged_config['resources']['initial_product']['initial_key'] == 'initial_value'
    assert 'test_product' in merged_config['resources']
    assert 'test_key' in merged_config['resources']['test_product']
    assert merged_config['resources']['test_product']['test_key'] == 'test_value'


def test__create_resource_from_odc_product():
    product = pickle.load(open('./data/product.pickle', 'rb'))
    bbox = datacube.utils.geometry.BoundingBox.from_points([1.0,2.0], [3.0,4.0])
    created_resource = _create_resource_from_odc_product(product,bbox)
    assert created_resource['type'] == 'collection'
    assert created_resource['title'] == 'dsm__MB__The_Pas_2014'
    assert created_resource['description'] == '"dsm" data created by "MB" within the project "The_Pas_2014"'
    assert isinstance(created_resource['extents'], dict)
    assert created_resource['extents']['spatial'] is not None
    assert created_resource['extents']['spatial']['bbox'] is not None
    assert len(created_resource['extents']['spatial']['bbox']) == 4
    assert created_resource['extents']['spatial']['bbox'][0] == 1.0
    assert created_resource['extents']['spatial']['bbox'][1] == 2.0
    assert created_resource['extents']['spatial']['bbox'][2] == 3.0
    assert created_resource['extents']['spatial']['bbox'][3] == 4.0
    assert created_resource['extents']['spatial']['crs'] == 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
    assert created_resource['providers'] is not None
    assert len(created_resource['providers']) == 1
    assert created_resource['providers'][0]['type'] == 'coverage'
    assert created_resource['providers'][0]['name'] == 'odcprovider.OpenDataCubeCoveragesProvider'
    assert created_resource['providers'][0]['data'] == 'dsm__MB__The_Pas_2014'
    assert created_resource['providers'][0]['format'] is not None
    assert created_resource['providers'][0]['format']['name'] == 'NetCDF'
    assert created_resource['providers'][0]['format']['mimetype'] == 'application/netcdf'
    assert len(created_resource['keywords']) == 6
    assert created_resource['keywords'][0] == 'MB'
    assert created_resource['keywords'][1] == 'dsm'
    assert created_resource['keywords'][2] == 'The_Pas_2014'
    assert created_resource['keywords'][3] == 'Canada'
    assert created_resource['keywords'][4] == 'NRCAN'
    assert created_resource['keywords'][5] == 'OGC Testbed 17'
    assert len(created_resource['links']) == 1
    assert created_resource['links'][0]['type'] == 'text/html'
    assert created_resource['links'][0]['rel'] == 'canonical'
    assert created_resource['links'][0]['title'] == 'High Resolution Digital Elevation Model (HRDEM) - CanElevation Series'
    assert created_resource['links'][0]['href'] == 'https://open.canada.ca/data/en/dataset/957782bf-847c-4644-a757-e383c0057995'
    assert created_resource['links'][0]['hreflang'] == 'en-CA'


def test__create_resource_from_odc_product_without_links():
    product = pickle.load(open('./data/product_without-keywords-and-links.pickle', 'rb'))
    bbox = datacube.utils.geometry.BoundingBox.from_points([1.0, 2.0], [3.0, 4.0])
    created_resource = _create_resource_from_odc_product(product, bbox)
    assert len(created_resource['links']) == 0


def test__create_resource_from_odc_product_without_keywords():
    product = pickle.load(open('./data/product_without-keywords-and-links.pickle', 'rb'))
    bbox = datacube.utils.geometry.BoundingBox.from_points([1.0, 2.0], [3.0, 4.0])
    created_resource = _create_resource_from_odc_product(product, bbox)
    assert len(created_resource['keywords']) == 0
