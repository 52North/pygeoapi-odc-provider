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
                                    ProviderConnectionError,
                                    ProviderQueryError,
                                    ProviderItemNotFoundError)

LOGGER = logging.getLogger(__name__)

class OpenDataCubeRecordsProvider(BaseProvider):
    """
    OGC API Records provider for an OpenDataCube instance
    """

    def __init__(self, provider_def):
        """
        Initialize the OpenDataCubeRecordsProvider

        :param provider_def: provider definition

        :returns odcprovider.OpenDataCubeRecordsProvider
        """

        super().__init__(provider_def)

        self.dc = datacube.Datacube(app='pygeoapi_provider')

        LOGGER.debug("Provider initiated: name: '{}', type: '{}', data: '{}'".format(self.name, self.type, self.data))
