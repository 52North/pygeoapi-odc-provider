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

import datacube
from pygeoapi.provider.base import (BaseProvider,
                                    ProviderGenericError,
                                    ProviderConnectionError,
                                    ProviderQueryError,
                                    ProviderItemNotFoundError)

LOGGER = logging.getLogger(__name__)

class OpenDataCubeRecordsProvider(BaseProvider):
    """
    OGC API Records provider for an OpenDataCube instance

    Each OpenDataCube product family is one collection, hence we have one record per collection per dataset
    """

    def __init__(self, provider_def):
        """
        Initialize the OpenDataCubeRecordsProvider

        :param provider_def: provider definition

        :returns odcprovider.OpenDataCubeRecordsProvider
        """

        super().__init__(provider_def)

        self.dc = datacube.Datacube(app='pygeoapi_provider')

        products = [d['name'] for d in self.dc.list_products(with_pandas=False)]

        if self.data not in products:
            raise ProviderGenericError("Configured product '{}' is not contained in OpenDataCube instance")

        LOGGER.debug("Provider initiated: name: '{}', type: '{}', data: '{}'".format(self.name, self.type, self.data))

    def query(self, startindex=0, limit=10, resulttype='results',
              bbox=[], datetime_=None, properties=[], sortby=[],
              select_properties=[], skip_geometry=False, q=None, **kwargs):
        """
        query TinyDB document store
        :param startindex: starting record to return (default 0)
        :param limit: number of records to return (default 10)
        :param resulttype: return results or hit limit (default results)
        :param bbox: bounding box [minx,miny,maxx,maxy]
        :param datetime_: temporal (datestamp or extent)
        :param properties: list of tuples (name, value)
        :param sortby: list of dicts (property, order)
        :param select_properties: list of property names
        :param skip_geometry: bool of whether to skip geometry (default False)
        :param q: full-text search term(s)
        :returns: dict of 0..n GeoJSON feature collection
        """

        # {
        # 'id': 1,
        # 'name': 'dsm__MB__The_Pas_2014',
        # 'description': '"dsm" data created by "MB" within the project "The_Pas_2014"',
        # 'creation_time': None,
        # 'format': None,
        # 'label': None,
        # 'lat': None,
        # 'lon': None,
        # 'time': None,
        # 'platform': None,
        # 'instrument': None,
        # 'region_code': None,
        # 'product_family': None,
        # 'dataset_maturity': None,
        # 'crs': 'EPSG:2957',
        # 'spatial_dimensions': ('y', 'x'),
        # 'tile_size': None,
        # 'resolution': (-1.0, 1.0)
        # }
        #
        # TODO woher den Spatial Extend des Products?
        # TODO datasets oder measurements auflisten? tendiere zu measurements
        # TODO woher weiß ich, in welcher Collection ich bin und daher, welches Produkt ich nehmen muss? z.Zt. Config -> data
        # self.data

        if limit < 1:
            raise ProviderQueryError("limit < 1 makes no sense!")

        product = self.dc.index.products.get_by_name(self.data)

        measurements = list(filter(lambda d: d['product'] in self.data,
                                   self.dc.list_measurements(with_pandas=False)))

        feature_collection = {
            'type': 'FeatureCollection',
            'features': []
        }

        return feature_collection