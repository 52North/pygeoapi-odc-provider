from pip._internal.req import parse_requirements
from setuptools import setup, find_packages

# loading requirements
requirements = list(parse_requirements('requirements.txt', session='hack'))
requirements = [r.requirement for r in requirements]

setup(
    name="pygeoapi-odc-provider",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "": ["*.txt"]
    },
    include_package_data=True,
    version="0.0.1",
    description="pygeoapi provider plugin for Open Data Cube",
    long_description="pygeoapi provider plugin for Open Data Cube",
    long_description_content_type="text/markdown",
    license="GNU General Public License version 2",
    url="",
    keywords=["ODC", "pygeoapi", "EO", "data cubes"],
    install_requires=requirements,
    test_suite="tests",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
