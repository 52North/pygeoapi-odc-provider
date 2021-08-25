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
# https://docs.python.org/3/distutils/setupscript.html
#
# =================================================================

from pip._internal.req import parse_requirements
from setuptools import setup, find_packages

# loading requirements
requirements = list(parse_requirements('requirements.txt', session='hack'))
requirements = [r.requirement for r in requirements]

setup(
    name="pygeoapi-odc-provider",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    version="0.3.0",
    description="pygeoapi provider plugin for Open Data Cube",
    long_description="pygeoapi provider plugin for Open Data Cube",
    long_description_content_type="text/markdown",
    license="Apache License, Version 2.0",
    url="",
    keywords=["ODC", "pygeoapi", "EO", "data cubes"],
    install_requires=requirements,
    test_suite="tests",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache License, Version 2.0',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
