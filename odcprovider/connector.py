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
import datacube

from datacube.utils.geometry import bbox_union

DEFAULT_APP = "pygeoapi_provider"


class OdcConnector():
    """
    Collection of convenience functions to interact with an OpenDataCube instance
    """

    def list_product_names(self):
        self._ensure_init()
        return [d['name'] for d in self.dc.list_products(with_pandas=False)]

    def _ensure_init(self):
        if self.dc is None:
            self.dc = datacube.Datacube(app='pygeoapi_provider')

    def load(self, product, **params):
        self._ensure_init()
        return self.dc.load(product=product, **params)

    def list_products(self, show_archived=False, with_pandas=True):
        self._ensure_init()
        return self.dc.list_products(show_archived=show_archived, with_pandas=with_pandas)

    def number_of_bands(self, product):
        self._ensure_init()
        return len(self.dc.index.products.get_by_name(product).measurements)

    def find_datasets(self, product, **search_terms):
        self._ensure_init()
        return self.dc.find_datasets(**search_terms)

    def list_measurements(self, show_archived=False, with_pandas=True):
        self._ensure_init()
        return self.dc.list_measurements(show_archived=show_archived, with_pandas=with_pandas)

    def bbox_of_product(self, product):
        self._ensure_init()
        if product is None:
            raise ValueError("product MUST not be None")
        if len(product) == 0:
            raise ValueError("product MUST not be an empty string")
        if not product in self.list_product_names():
            raise ValueError("product MUST be in datacube")

        bbs = []
        for dataset in self.dc.find_datasets(product=self.data):
            bbs.append(dataset.bounds)

        return bbox_union(bbs)