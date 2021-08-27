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
import logging
from typing import Any

import datacube
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
        self.dc = None

    def _ensure_init(self) -> None:
        if self.dc is None:
            self.dc = datacube.Datacube(app=DEFAULT_APP)

    def list_product_names(self) -> []:
        self._ensure_init()
        return [d['name'] for d in self.dc.list_products(with_pandas=False)]

    def load(self, product:str, **params) -> Any:
        self._ensure_init()
        return self.dc.load(product=product, **params)

    def list_products(self, show_archived:bool = False, with_pandas:bool = True) -> list:
        self._ensure_init()
        return self.dc.list_products(show_archived=show_archived, with_pandas=with_pandas)

    def number_of_bands(self, product:str) -> int:
        self._ensure_init()
        return len(self.dc.index.products.get_by_name(product).measurements)

    def find_datasets(self, **search_terms) -> list:
        self._ensure_init()
        return self.dc.find_datasets(**search_terms)

    def list_measurements(self, show_archived:bool = False, with_pandas:bool = True) -> DataFrame:
        self._ensure_init()
        return self.dc.list_measurements(show_archived=show_archived, with_pandas=with_pandas)

    def bbox_of_product(self, product:str) -> BoundingBox:
        """
        Get bounding box of a product
        :param product: product name
        :returns datacube.utils.geometry._base.BoundingBox
        """
        self._ensure_init()
        if product is None:
            raise ValueError("product MUST not be None")
        if len(product) == 0:
            raise ValueError("product MUST not be an empty string")
        if not product in self.list_product_names():
            raise ValueError("product MUST be in datacube")

        crs_set = self.get_crs_set(product=product)
        if len(crs_set) > 1:
            LOGGER.info('product {} has datasets with varying crs:'.format(product))
            for crs in crs_set:
                LOGGER.info('- {}'.format(str(crs)))
            LOGGER.info('reproject to WGS84.')

        bbs = []
        for dataset in self.find_datasets(product=product):
            if len(crs_set) == 1:
                bbs.append(dataset.bounds)
            else:
                bbs.append(convert_datacube_bbox_to_wgs84(dataset.bounds, str(dataset.crs)))

        return bbox_union(bbs)

    def get_product_by_id(self, identifier:str) -> DatasetType:
        self._ensure_init()
        return self.dc.index.products.get_by_name(name=identifier)

    def get_crs_set(self, product:str) -> set:
        crs_set= set()
        for dataset in self.dc.find_datasets(product=product):
            crs_set.add(dataset.crs)
        return crs_set

