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
    'version': '0.2.0',
    'id': 'hello-world',
    'title': {
        'en': 'Hello World',
        'fr': 'Bonjour le Monde'
    },
    'description': {
        'en': 'An example process that takes a name as input, and echoes '
              'it back as output. Intended to demonstrate a simple '
              'process with a single literal input.',
        'fr': 'Un exemple de processus qui prend un nom en entrée et le '
              'renvoie en sortie. Destiné à démontrer un processus '
              'simple avec une seule entrée littérale.',
    },
    'keywords': ['hello world', 'example', 'echo'],
    'links': [{
        'type': 'text/html',
        'rel': 'canonical',
        'title': 'information',
        'href': 'https://example.org/process',
        'hreflang': 'en-US'
    }],
    'inputs': [{
        'id': 'name',
        'title': 'Name',
        'abstract': 'The name of the person or entity that you wish to be'
                    'echoed back as an output',
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
        'keywords': ['full name', 'personal']
    }, {
        'id': 'message',
        'title': 'Message',
        'abstract': 'An optional message to echo as well',
        'input': {
            'literalDataDomain': {
                'dataType': 'string',
                'valueDefinition': {
                    'anyValue': True
                }
            }
        },
        'minOccurs': 0,
        'maxOccurs': 1,
        'metadata': None,
        'keywords': ['message']
    }],
    'outputs': [{
        'id': 'echo',
        'title': 'Hello, world',
        'description': 'A "hello world" echo with the name and (optional)'
                       'message submitted for processing',
        'output': {
            'formats': [{
                'mimeType': 'application/json'
            }]
        }
    }],
    'example': {
        'inputs': [{
            'id': 'name',
            'value': 'World',
            'type': 'text/plain'
        }, {
            'id': 'message',
            'value': 'An optional message.',
            'type': 'text/plain'
        }]
    }
}


class OpenDataCubeProviderProcesses(BaseProcessor):
    """Hello World Processor example"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: pygeoapi.process.hello_world.HelloWorldProcessor
        """

        super().__init__(processor_def, PROCESS_METADATA)

    def execute(self, data):

        mimetype = 'application/json'
        name = data.get('name', None)

        if name is None:
            raise ProcessorExecuteError('Cannot process without a name')

        value = 'Hello {}! {}'.format(name, data.get('message', '')).strip()

        outputs = [{
            'id': 'echo',
            'value': value
        }]

        return mimetype, outputs

    def __repr__(self):
        return '<HelloWorldProcessor> {}'.format(self.name)
