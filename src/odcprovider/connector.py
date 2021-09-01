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
from __future__ import annotations
import logging
from typing import Any, Union

from datacube import Datacube
from datacube.model import DatasetType
from datacube.utils.geometry import bbox_union, BoundingBox
from pandas import DataFrame

from .constants import DEFAULT_APP
from .utils import convert_datacube_bbox_to_wgs84

LOGGER = logging.getLogger(__name__)


class OdcConnector:
    """
    Collection of convenience functions to interact with an OpenDataCube instance
    """

    def __init__(self) -> None:
        self.dc = Datacube(app=DEFAULT_APP)
        self.metadatastore = OdcMetadataStore.instance(self.dc)

    def list_product_names(self) -> []:
        return self.metadatastore.list_product_names();

    def get_product_by_id(self, identifier: str) -> DatasetType:
        return self.metadatastore.get_product_by_id(identifier)

    def number_of_bands(self, product: str) -> int:
        return self.metadatastore.number_of_bands(product)

    def get_datasets_for_product(self, product:str) -> list:
        return self.metadatastore.find_datasets(product)

    def list_measurements(self) -> DataFrame:
        return self.metadatastore.list_measurements()

    def bbox_of_product(self, product: str) -> BoundingBox:
        return self.metadatastore.bbox_of_product(product)

    def get_crs_set(self, product: str) -> set:
        return self.metadatastore.get_crs_set(product)

    def load(self, product: str, **params) -> Any:
        return self.dc.load(product=product, **params)


class OdcMetadataStore():
    """
    Stores not changing metadata of the accessed OpenDataCube instance.
    Implementation uses singleton pattern to improve performance when
    accessing the metadata.
    Implementation follows:

        https://python-patterns.guide/gang-of-four/singleton/
    """

    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls, dc:Datacube) -> OdcMetadataStore:
        LOGGER.debug("instance() called")
        if dc is None or not isinstance(dc, Datacube):
            raise RuntimeError('required Datacube object not received')
        if cls._instance is None:
            LOGGER.debug("Creating instance of class '{}'".format(cls))
            cls._instance = cls.__new__(cls)
            # init variables
            cls._init_cache(dc)
        else:
            LOGGER.debug("Instance of class '{}' already existing".format(cls))
        return cls._instance

    @classmethod
    def _init_cache(cls, dc:Datacube) -> None:
        LOGGER.debug("_init_cache() called")
        cls._instance.product_names = [d['name'] for d in dc.list_products(with_pandas=False)]
        cls._instance.products_by_identifier = cls._create_identifier_product_map(dc)
        cls._instance.datasets_by_product_identifier = cls._create_product_dataset_map(dc)
        cls._instance.measurements_complex_without_archived = cls._get_complex_active_measurements(dc)
        cls._instance.crs_set_by_product_identifier = cls._get_crs_set_for_all_products(dc)
        cls._instance.bboxes_by_product_identifier = cls._get_bboxes_for_all_products(dc)

    @classmethod
    def _create_identifier_product_map(cls, dc:Datacube) -> dict:
        map = dict()
        for product in cls._instance.product_names:
            map[product] = dc.index.products.get_by_name(product)
        return map

    @classmethod
    def _create_product_dataset_map(cls, dc:Datacube) -> dict:
        map = dict()
        for product in cls._instance.product_names:
            map[product] = dc.find_datasets(product=product)
        return map

    @classmethod
    def _get_complex_active_measurements(cls, dc:Datacube) -> DataFrame:
        return dc.list_measurements(show_archived=False, with_pandas=True)

    @classmethod
    def _get_crs_set_for_all_products(cls, dc:Datacube) -> dict:
        map = dict()
        for product in cls._instance.product_names:
            crs_set = set()
            for dataset in cls._instance.datasets_by_product_identifier[product]:
                crs_set.add(dataset.crs)
            map[product] = crs_set
        return map

    @classmethod
    def _get_bboxes_for_all_products(cls, dc:Datacube) -> dict:
        map = dict()
        for product in cls._instance.product_names:
            crs_set = cls._instance.crs_set_by_product_identifier[product]
            if len(crs_set) > 1:
                LOGGER.info('product {} has datasets with varying crs:'.format(product))
                for crs in crs_set:
                    LOGGER.info('- {}'.format(str(crs)))
                LOGGER.info('reproject to WGS84.')

            bbs = []
            for dataset in cls._instance.datasets_by_product_identifier[product]:
                if len(crs_set) == 1:
                    bbs.append(dataset.bounds)
                else:
                    bbs.append(convert_datacube_bbox_to_wgs84(dataset.bounds, str(dataset.crs)))

            map[product] = bbox_union(bbs)

        return map

    def list_product_names(self) -> list:
        return self.product_names;

    def get_product_by_id(self, identifier) -> DatasetType:
        return self.products_by_identifier[identifier]

    def number_of_bands(self, product) -> int:
        return len(self.products_by_identifier[product].measurements)

    def find_datasets(self, product):
        return self.datasets_by_product_identifier[product]

    def list_measurements(self):
        return self.measurements_complex_without_archived

    def bbox_of_product(self, product:str) -> BoundingBox:
        """
        Get bounding box of a product
        :param product: product name
        :returns datacube.utils.geometry._base.BoundingBox
        """
        if product is None:
            raise ValueError("product MUST not be None")
        if len(product) == 0:
            raise ValueError("product MUST not be an empty string")
        if product not in self.product_names:
            raise ValueError("product MUST be in datacube")
        return self.bboxes_by_product_identifier[product]

    def get_crs_set(self, product):
        return self.crs_set_by_product_identifier[product]
