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
        'href': 'https://github.com/geopython/pygeoapi/blob/master/pygeoapi/process/hello_world.py',
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


class HelloWorldProcessor(BaseProcessor):
    """Hello World Processor example"""

    def __init__(self, processor_def):
        """
        Initialize object
        :param processor_def: provider definition
        :returns: odcprovider.HelloWorldProcessor
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
