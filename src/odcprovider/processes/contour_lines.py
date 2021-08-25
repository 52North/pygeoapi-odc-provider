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
#
# =================================================================
#
# Dummy Process to test with deployment based on
#
#     https://github.com/geopython/pygeoapi/blob/master/pygeoapi/process/hello_world.py
#
#

import logging

from pygeoapi.process.base import (BaseProcessor, ProcessorExecuteError)

LOGGER = logging.getLogger(__name__)

# : Process metadata and description
PROCESS_METADATA = {
    'version': '0.1.0',
    'id': 'contour-lines',
    'title': {
        'en': 'Contour Lines'
    },
    'description': {
        'en': 'An process that takes a product name '
              'and some additional parameters and generates '
              'a contour lines shapefile.'
    },
    'keywords': ['DEM', 'Digital Elevation Model', 'DSM', 'Digital Surface Model', 'contour', 'contour lines'],
    'links': [{
        'type': 'text/html',
        'rel': 'canonical',
        'title': 'information',
        'href': 'https://gdal.org/programs/gdal_contour.html',
        'hreflang': 'en-US'
    }],
    'inputs': [{
        'id': 'product',
        'title': 'Product',
        'abstract': 'The name of the product in the data cube to use'
                    'for generating the contour line shape file',
        'input': {
            'literalDataDomain': {
                'dataType': 'string',
                'valueDefinition': {
                    'anyValue': True
                }
            }
        },
        'minOccurs': 1,
        'maxOccurs': 1,
        'metadata': None,  # TODO how to use?
        'keywords': None
    }],
    'outputs': [{
        'id': 'contour-lines-shape-file',
        'title': 'Contour Lines Shape File',
        'description': 'The resulting contour lines shape file',
        'output': {
            'formats': [{
                'mimeType': 'x-gis/x-shapefile'
            }]
        }
    }],
    'example': {
        'inputs': [{
            'id': 'product',
            'value': 'dsm__MB__The_Pas_2014',
            'type': 'text/plain'
        }]
    }
}


class ContourLinesProcessor(BaseProcessor):
    """Contour Lines Processor"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: odcprovider.ContourLinesProcessor
        """

        super().__init__(processor_def, PROCESS_METADATA)

    def execute(self, data):

        mimetype = 'application/json'
        product = data.get('product', None)

        if product is None:
            raise ProcessorExecuteError('Cannot process without a product')

        value = 'Hello {}! {}'.format(product, data.get('message', '')).strip()

        outputs = [{
            'id': 'contour-lines-shape-file',
            'value': value
        }]

        return mimetype, outputs

    def __repr__(self):
        return '<ContourLinesProcessor> {}'.format(self.name)
