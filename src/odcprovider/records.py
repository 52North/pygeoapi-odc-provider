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
import datetime
import logging

from .connector import OdcConnector
from .utils import convert_datacube_bbox_to_geojson_wgs84_polygon
from pygeoapi.provider.base import (BaseProvider,
                                    ProviderGenericError,
                                    ProviderConnectionError,
                                    ProviderQueryError,
                                    ProviderItemNotFoundError)

LOGGER = logging.getLogger(__name__)


class OpenDataCubeRecordsProvider(BaseProvider):
    """
    OGC API Records provider for an OpenDataCube instance

    This provider MUST be used in its own pygeoapi collection and not as part of
    an already existing data containing collection.
    """

    def __init__(self, provider_def):
        """
        Initialize the OpenDataCubeRecordsProvider

        :param provider_def: provider definition

        :returns odcprovider.OpenDataCubeRecordsProvider
        """

        super().__init__(provider_def)

        self.dc = OdcConnector()

        LOGGER.debug("Provider initiated: name: '{}', type: '{}', data: '{}'".format(self.name, self.type, self.data))

    def query(self, startindex=0, limit=10, resulttype='results',
              bbox=[], datetime_=None, properties=[], sortby=[],
              select_properties=[], skip_geometry=False, q=None, **kwargs):
        """
        query OpenDataCube products
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

        if limit < 1:
            raise ProviderQueryError("limit < 1 makes no sense!")

        if startindex < 0:
            raise ProviderQueryError("startIndex < 0 makes no sense!")

        features = []
        for product in self.dc.list_products(with_pandas=False):
            features.append(self._encode_as_record(product))

        # apply limit and start index
        all_count = len(features)
        if len(features) > limit:
            features = features[startindex:(startindex+limit)]

        feature_collection = {
            'type': 'FeatureCollection',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'numberMatched': all_count,
            'numberReturned': len(features),
            'features': features
        }

        if resulttype == 'hit limit':
            return len(features)
        else:
            return feature_collection

    def get(self, identifier, **kwargs):
        """
        Get OpenDataCube product family by id

        :param identifier: family id

        :returns: `dict` of single record
        """
        LOGGER.debug('Fetching identifier {}'.format(identifier))

        return self._encode_dataset_type_as_record(self.dc.get_product_by_id(identifier))

    def _encode_as_record(self, product):
        # product = self.dc.index.products.get_by_name(self.data)
        #
        # measurements = list(filter(lambda d: d['product'] in self.data,
        #                            self.dc.list_measurements(with_pandas=False)))
        #
        # features = [{
        #     'id': product.name,
        #     'properties': [
        #
        #     ]
        # }]
        return {
            'id': product.get('name'),
            'properties': self._encode_record_properties(product)
        }

    def _encode_record_properties(self, product):
        properties = {}

        for property in product.keys():
            properties.update({property: product.get(property)})

        # properties derived via datacube.utils.documents.DocReader
        # TODO verify properties.update(product.metadata.fields)

        return properties

    def _encode_dataset_type_as_record(self, product):
        return {
            'id': product.name,
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': convert_datacube_bbox_to_geojson_wgs84_polygon(self.dc.bbox_of_product(product.name),
                                       'epsg:' + str(product.grid_spec.crs.to_epsg()))
            },
            'properties': self._encode_dataset_type_properties(product)
        }

    def _encode_dataset_type_properties(self, product):
        properties = {}
        # properties from metadata doc
        for metadata_key in product.metadata_doc.keys():
            properties.update({metadata_key: product.metadata_doc.get(metadata_key).get('name')})

        # properties derived via datacube.utils.documents.DocReader
        properties.update(product.metadata.fields)

        return properties