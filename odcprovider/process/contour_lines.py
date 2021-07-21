# =================================================================
# Copyright (C) 2021-2021 52°North Spatial Information Research GmbH
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# If the program is linked with libraries which are licensed under one of
# the following licenses, the combination of the program with the linked
# library is not considered a "derivative work" of the program:
#
#     - Apache License, version 2.0
#     - Apache Software License, version 1.0
#     - GNU Lesser General Public License, version 3
#     - Mozilla Public License, versions 1.0, 1.1 and 2.0
#     - Common Development and Distribution License (CDDL), version 1.0
#
# Therefore the distribution of the program linked with libraries licensed
# under the aforementioned licenses, is permitted by the copyright holders
# if the distribution is compliant with both the GNU General Public
# License version 2 and the aforementioned licenses.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
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
        :returns: odcprovider.process.contour_lines.ContourLinesProcessor
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
