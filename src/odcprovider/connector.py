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
from pathlib import Path
import os
from typing import Any

import pickle

import xarray
from datacube import Datacube
from datacube.model import DatasetType, Dataset
from datacube.utils.geometry import bbox_union, BoundingBox, CRS
from pandas import DataFrame

from .constants import DEFAULT_APP, CACHE_PICKLE
from .utils import convert_datacube_bbox_to_wgs84


LOGGER = logging.getLogger(__name__)


class OdcConnector:
    """
    Collection of convenience functions to interact with an OpenDataCube instance
    """

    def __init__(self) -> None:
        self.dc = Datacube(app=DEFAULT_APP)
        self.metadata_store = OdcMetadataStore.instance(self.dc, CACHE_PICKLE)

    def list_product_names(self) -> []:
        return self.metadata_store.list_product_names()

    def get_product_by_id(self, identifier: str) -> DatasetType:
        return self.metadata_store.get_product_by_id(identifier)

    def number_of_bands(self, product: str) -> int:
        return self.metadata_store.number_of_bands(product)

    def get_datasets_for_product(self, product: str) -> list[Dataset]:
        return self.metadata_store.find_datasets(product)

    def list_measurements(self) -> DataFrame:
        return self.metadata_store.list_measurements()

    def bbox_of_product(self, product: str) -> BoundingBox:
        return self.metadata_store.bbox_of_product(product)

    def get_crs_set(self, product: str) -> set:
        return self.metadata_store.get_crs_set(product)

    def get_resolution_set(self, product: str) -> set:
        return self.metadata_store.get_resolution_set(product)

    def wgs84_bbox_of_product(self, product: str) -> BoundingBox:
        return self.metadata_store.wgs84_bbox_of_product(product)

    def load(self, product: str, **params) -> xarray.Dataset:
        return self.dc.load(product=product, **params)


class OdcMetadataStore:
    """
    Stores not changing metadata of the accessed OpenDataCube instance.
    Implementation uses singleton pattern to improve performance when
    accessing the metadata.
    Implementation follows:

        https://python-patterns.guide/gang-of-four/singleton/
    """

    _instance = None

    def __init__(self):
        self.wgs84_bboxes_by_product_identifier = None
        self.crs_set_by_product_identifier = None
        self.resolution_set_by_product_identifier = None
        self.product_names = None
        self.bboxes_by_product_identifier = None
        self.measurements_complex_without_archived = None
        self.datasets_by_product_identifier = None
        self.products_by_identifier = None
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls, dc: Datacube, cache_pickle: str) -> OdcMetadataStore:
        LOGGER.debug("instance() called")
        if dc is None or not isinstance(dc, Datacube):
            raise RuntimeError('required Datacube object not received')
        if cls._instance is None:
            LOGGER.debug("Creating instance of class '{}'...".format(cls))
            pickle_path = Path(cache_pickle).resolve()
            if os.path.exists(pickle_path) and os.access(pickle_path, mode=os.R_OK | os.W_OK):
                # 1 try to load pickle from previous runs
                LOGGER.debug('from pickle...')
                cls._instance = pickle.load(open(pickle_path, 'rb'))
                LOGGER.debug('...DONE.')
            else:
                # 2 init from datacube
                LOGGER.debug('from datacube...')
                cls._instance = cls.__new__(cls)
                # init variables
                cls._init_cache(dc)
                pickle.dump(cls._instance, open(pickle_path, 'wb'))
                LOGGER.debug('...DONE.')
        else:
            LOGGER.debug("Instance of class '{}' already existing".format(cls))
        return cls._instance

    @classmethod
    def _init_cache(cls, dc: Datacube) -> None:
        LOGGER.debug("_init_cache() called")
        cls._instance.product_names = [d['name'] for d in dc.list_products(with_pandas=False)]
        cls._instance.products_by_identifier = cls._create_identifier_product_map(dc)
        cls._instance.datasets_by_product_identifier = cls._create_product_dataset_map(dc)
        cls._instance.measurements_complex_without_archived = cls._get_complex_active_measurements(dc)
        cls._instance.crs_set_by_product_identifier = cls._get_crs_set_for_all_products()
        cls._instance.resolution_set_by_product_identifier = cls._get_resolution_set_for_all_products()
        cls._instance.bboxes_by_product_identifier = cls._get_bboxes_for_all_products()
        cls._instance.wgs84_bboxes_by_product_identifier = cls._get_wgs84_bboxes_for_all_products()

    @classmethod
    def _create_identifier_product_map(cls, dc: Datacube) -> dict:
        product_map = dict()
        for product in cls._instance.product_names:
            product_map[product] = dc.index.products.get_by_name(product)
        return product_map

    @classmethod
    def _create_product_dataset_map(cls, dc: Datacube) -> dict:
        dataset_map = dict()
        for product in cls._instance.product_names:
            dataset_map[product] = dc.find_datasets(product=product)
        return dataset_map

    @classmethod
    def _get_complex_active_measurements(cls, dc: Datacube) -> DataFrame:
        if len(dc.list_measurements(show_archived=False, with_pandas=False)) == 0:
            return DataFrame(columns=['name', 'dtype', 'units', 'nodata', 'aliases'])
        else:
            # With 'with_pandas=True' a KeyError is raised if there are no measurements:
            #   KeyError: "None of ['product', 'measurement'] are in the columns"
            return dc.list_measurements(show_archived=False, with_pandas=True)

    @classmethod
    def _get_crs_set_for_all_products(cls) -> dict:
        crs_set_map = dict()
        for product in cls._instance.product_names:
            crs_set = set()
            for dataset in cls._instance.datasets_by_product_identifier[product]:
                crs_set.add(dataset.crs)
            crs_set_map[product] = crs_set
        return crs_set_map

    @classmethod
    def _get_resolution_set_for_all_products(cls) -> dict:
        resolution_set_map = dict()
        for product in cls._instance.product_names:
            resolution_set = set()
            for dataset in cls._instance.datasets_by_product_identifier[product]:
                # Add (resolution x, resolution y) to set for each dataset
                # Keep sign because Open Data Cube needs this information when loading data
                # ToDo: There may be other grids than the default grid,
                #       see https://datacube-core.readthedocs.io/en/latest/ops/dataset_documents.html#eo3-format.
                #       These should be included later.
                resolution_set.add((dataset.metadata_doc['grids']['default']['transform'][0],
                                    dataset.metadata_doc['grids']['default']['transform'][4]))
            resolution_set_map[product] = resolution_set
        return resolution_set_map

    @classmethod
    def _get_bboxes_for_all_products(cls) -> dict:
        bbox_map = dict()
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

            bbox_map[product] = bbox_union(bbs)

        return bbox_map

    @classmethod
    def _get_wgs84_bboxes_for_all_products(cls) -> dict:
        wgs84_bboxes = {}
        wgs84 = CRS('epsg:4326')

        for product in cls._instance.product_names:
            crs_set = cls._instance.crs_set_by_product_identifier[product]
            if len(crs_set) == 1 and wgs84 not in crs_set:
                wgs84_bboxes.update(
                    {
                        product: convert_datacube_bbox_to_wgs84(cls._instance.bboxes_by_product_identifier[product],
                                                                next(iter(crs_set)))
                    }
                )
            else:
                # if len(crs_set) > 1 => the bbox is already in wgs84 by _get_bboxes_for_all_products
                wgs84_bboxes.update(
                    {
                        product: cls._instance.bboxes_by_product_identifier[product]
                    }
                )

        return wgs84_bboxes

    def list_product_names(self) -> list:
        return self.product_names

    def get_product_by_id(self, identifier: str) -> DatasetType:
        self.check_product_parameter(identifier)
        return self.products_by_identifier[identifier]

    def number_of_bands(self, product: str) -> int:
        self.check_product_parameter(product)
        return len(self.products_by_identifier[product].measurements)

    def find_datasets(self, product: str) -> list:
        self.check_product_parameter(product)
        return self.datasets_by_product_identifier[product]

    def list_measurements(self) -> DataFrame:
        return self.measurements_complex_without_archived

    def bbox_of_product(self, product: str) -> BoundingBox:
        self.check_product_parameter(product)
        return self.bboxes_by_product_identifier[product]

    def check_product_parameter(self, product: str) -> None:
        if product is None:
            raise ValueError("product MUST not be None")
        if len(product) == 0:
            raise ValueError("product MUST not be an empty string")
        if product not in self.product_names:
            raise ValueError("product MUST be in datacube")

    def get_crs_set(self, product: str) -> set:
        self.check_product_parameter(product)
        return self.crs_set_by_product_identifier[product]

    def get_resolution_set(self, product: str) -> set:
        self.check_product_parameter(product)
        return self.resolution_set_by_product_identifier[product]

    def wgs84_bbox_of_product(self, product: str) -> BoundingBox:
        self.check_product_parameter(product)
        return self.wgs84_bboxes_by_product_identifier[product]
