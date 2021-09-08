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
import pickle

import tests.test_connector
from src.odcprovider.records import OpenDataCubeRecordsProvider
from .test_connector import DatacubeMock


class OpenDataCubeRecordsProviderMock(OpenDataCubeRecordsProvider):

    def __init__(self):
        self.dc = DatacubeMock()


def test__encode_dataset_type_as_record():
    product_to_encode = pickle.load(open("./data/product_1.pickle", "rb"))
    mock = OpenDataCubeRecordsProviderMock()
    encoded_product = mock._encode_dataset_type_as_record(product_to_encode)

    assert encoded_product.get('id') == product_to_encode.name


def test__encode_dataset_type_properties():
    product_to_encode = pickle.load(open("./data/product_1.pickle", "rb"))
    mock = OpenDataCubeRecordsProviderMock()
    encoded_product_properties = mock._encode_dataset_type_properties(product_to_encode)

    assert encoded_product_properties.get('product') is not None
    assert encoded_product_properties.get('product') == product_to_encode.name
    assert encoded_product_properties.get('project') is not None
    assert encoded_product_properties.get('project') == product_to_encode.metadata_doc.get('project').get('name')
    assert encoded_product_properties.get('provider') is not None
    assert encoded_product_properties.get('provider') == product_to_encode.metadata_doc.get('provider').get('name')
    assert encoded_product_properties.get('category') is not None
    assert encoded_product_properties.get('category') == product_to_encode.metadata_doc.get('category').get('name')
    assert encoded_product_properties.get('keywords') is not None
    assert encoded_product_properties.get('keywords') == product_to_encode.metadata_doc.get('keywords')
