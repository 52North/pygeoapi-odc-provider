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
from src.create_config import _merge_config
from tempfile import NamedTemporaryFile
import yaml

# def test_create_config():
#     assert False

def test_merge_config():
    # _merge_config()
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

