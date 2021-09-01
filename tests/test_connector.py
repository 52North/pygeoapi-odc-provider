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
from typing import Union

from datacube import Datacube
from datacube.model import DatasetType, Dataset
from datacube.utils.geometry import CRS, BoundingBox
from pandas import DataFrame

from src.odcprovider.connector import OdcMetadataStore


def test_odc_metadata_store_instance_raise_error_on_missing_parameter():

    expected_error_message = 'required Datacube object not received'
    try:
        OdcMetadataStore.instance(None)
        assert False

    except RuntimeError as e:
        assert str(e) == expected_error_message

    try:
        OdcMetadataStore.instance(dict())
        assert False

    except RuntimeError as e:
        assert str(e) == expected_error_message


def test_odc_metadata_store__init__raises_error():
    try:
        OdcMetadataStore()
    except RuntimeError as e:
        assert str(e) == 'Call instance() instead'


def test_odc_metadata_store_list_product_names():
    store = OdcMetadataStore.instance(DatacubeMock())

    def check(obj):
        assert obj is not None
        assert isinstance(obj, list)
        assert len(obj) == 2
        assert obj[0] == 'dsm__NRCAN__Edmonton_2018'
        assert obj[1] == 'dsm__MB__The_Pas_2014'

    check(store.product_names)
    check(store.list_product_names())


def test_odc_metadata_store_get_product_by_id():
    store = OdcMetadataStore.instance(DatacubeMock())

    received_product = store.get_product_by_id('dsm__NRCAN__Edmonton_2018')

    assert received_product is not None
    assert isinstance(received_product, DatasetType)
    assert received_product.name == 'dsm__NRCAN__Edmonton_2018'
    assert received_product.metadata_doc.get('project').get('name') == 'Edmonton_2018'


def test_odc_metadata_store_number_of_bands():
    store = OdcMetadataStore.instance(DatacubeMock())

    bands_count = store.number_of_bands('dsm__NRCAN__Edmonton_2018')

    assert bands_count == 1


def test_odc_metadata_store_find_datasets():
    store = OdcMetadataStore.instance(DatacubeMock())

    received_datasets = store.find_datasets('dsm__NRCAN__Edmonton_2018')

    assert received_datasets is not None
    assert isinstance(received_datasets, list)
    assert len(received_datasets) == 13
    dataset_to_check = received_datasets[2]
    assert dataset_to_check is not None
    assert isinstance(dataset_to_check, Dataset)
    assert str(dataset_to_check.id) == 'cfb39699-4665-57d3-8aa6-b56b62bce226'


def test_odc_metadata_store_list_measurements():
    store = OdcMetadataStore.instance(DatacubeMock())

    received_measurements = store.list_measurements()

    assert received_measurements is not None
    assert isinstance(received_measurements, DataFrame)
    assert len(received_measurements) == 2
    assert received_measurements.iloc[1]['name'] == 'dsm'
    assert received_measurements.iloc[1]['units'] == 'm'
    assert received_measurements.iloc[1]['dtype'] == 'float32'
    assert received_measurements.iloc[1]['nodata'] == -32767.0


def test_odc_metadata_store_get_crs_set():
    store = OdcMetadataStore.instance(DatacubeMock())

    received_crs_set = store.get_crs_set('dsm__NRCAN__Edmonton_2018')

    assert received_crs_set is not None
    assert isinstance(received_crs_set, set)
    assert len(received_crs_set) == 1
    crs = received_crs_set.pop()
    assert isinstance(crs, CRS)
    assert str(crs) == 'EPSG:2955'


def test_odc_metadata_store_bbox_of_product():
    store = OdcMetadataStore.instance(DatacubeMock())

    received_bbox = store.bbox_of_product('dsm__NRCAN__Edmonton_2018')

    assert received_bbox is not None
    assert isinstance(received_bbox, BoundingBox)
    assert received_bbox.width == 20000
    assert received_bbox.height == 80000
    assert received_bbox.left == 700000.0
    assert received_bbox.right == 720000.0
    assert received_bbox.top == 5970000.0
    assert received_bbox.bottom == 5890000.0


def test_odc_metadata_store_bbox_of_product_error_handling():
    store = OdcMetadataStore.instance(DatacubeMock())

    try:
        store.bbox_of_product(None)
        assert False
    except ValueError as e:
        assert str(e) == 'product MUST not be None'

    try:
        store.bbox_of_product('')
        assert False
    except ValueError as e:
        assert str(e) == 'product MUST not be an empty string'

    try:
        store.bbox_of_product('not_contained_product')
        assert False
    except ValueError as e:
        assert str(e) == 'product MUST be in datacube'

class ProductsMock:
    def get_by_name(self, product:str) -> DatasetType:
        if product == 'dsm__NRCAN__Edmonton_2018':
            return pickle.load(open("./data/product_2.pickle", "rb"))
        elif product == 'dsm__MB__The_Pas_2014':
            return pickle.load(open("./data/product_1.pickle", "rb"))
        else:
            raise RuntimeError("product with id '{}' not found".format(product))


class IndexMock:
    def __init__(self):
        self.products = ProductsMock()


class DatacubeMock(Datacube):
    def __init__(self):
        self.index = IndexMock()
        self.products = pickle.load(open("./data/products_as_pandas.pickle", "rb"))

    def list_products(self, show_archived: bool = False, with_pandas: bool = False) -> Union[list, DataFrame, None]:
        if not with_pandas:
            return [{ "name":"dsm__NRCAN__Edmonton_2018"}, { "name":"dsm__MB__The_Pas_2014"}]
        else:
            return self.products

    def find_datasets(self, product:str) -> list:
        if product == 'dsm__NRCAN__Edmonton_2018':
            return pickle.load(open("./data/datasets_2.pickle", "rb"))
        elif product == 'dsm__MB__The_Pas_2014':
            return pickle.load(open("./data/datasets_1.pickle", "rb"))
        else:
            raise RuntimeError("datasets for product with id '{}' not found".format(product))

    def list_measurements(self, show_archived=False, with_pandas=True) -> DataFrame:
        return pickle.load(open("./data/measurements.pickle", "rb"))
