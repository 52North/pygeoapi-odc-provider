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
# Convenience script to create resource entries for each datacube product to be included in pygeoapi's config.yml
# =================================================================
import logging
import os

from pathlib import Path

import yaml
import argparse
from odcprovider.connector import OdcConnector
from odcprovider.utils import convert_datacube_bbox_to_wgs84
from datacube.utils.geometry import BoundingBox
from datacube.model import DatasetType

logging_config_file = Path(Path(__file__).parent, 'logging.yaml')
level = logging.DEBUG
if os.path.exists(logging_config_file):
    with open(logging_config_file, 'rt') as file:
        try:
            config = yaml.safe_load(file.read())
            logging.config.dictConfig(config)
        except Exception as e:
            print(e)
            print('Error while loading logging configuration from file "{}". Using defaults'
                  .format(logging_config_file))
            logging.basicConfig(level=level)
else:
    print('Logging file configuration does not exist: "{}". Using defaults.'.format(logging_config_file))
    logging.basicConfig(level=level)

LOGGER = logging.getLogger(__name__)

# ToDo: improve formatting of created config.yaml


def parse_parameter() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Create resource entries for pygeoapi configuration. If infile is '
                    'provided, resource entries will be inserted there and written to outfile.')
    parser.add_argument('--infile', '-i',
                        help='File name of the config yaml that should be merged.')
    parser.add_argument('--outfile', '-o',
                        default='config_auto.yml',
                        help='Output yaml file name (default: config_auto.yml)')
    parser.add_argument('--exclude-products',
                        help='Comma separated list of product names to exclude')
    args = parser.parse_args()

    if args.exclude_products:
        args.exclude_products = [s.strip() for s in args.exclude_products.split(",")]

    LOGGER.info("""
Start creating pygeoapi config
==============================
- empty values are allowed

infile            : {}
outfile           : {}
exclude products  : {}""".format(args.infile, args.outfile, args.exclude_products))

    return args


def _create_resource_from_odc_product(product: DatasetType, bbox: BoundingBox, format_set: set) -> dict:
    """
    Create resource from Open Data Cube product

    :param product: ODC product, datacube.model.DatasetType
    :param bbox: bbox in WGS84!!!
    :param format_set: set of format strings (e.g. 'GeoTIFF' or 'netCDF')
    :return: dict
    """

    left, bottom, right, top = bbox
    if product.fields['format'] is not None:
        format_name = product.fields['format']
    elif len(format_set) == 1:
        format_name = next(iter(format_set))
    else:
        format_name = 'GeoTIFF'

    links = []
    if 'links' in product.metadata_doc.keys():
        for link in product.metadata_doc.get('links'):
            links.append({
                'type': link.get('type'),
                'rel': link.get('rel'),
                'title': link.get('title'),
                'href': link.get('href'),
                'hreflang': link.get('hreflang')
            })

    resource_dict = {
        'type': 'collection',
        'title': product.name,
        'description': product.definition['description'],
        'keywords': product.metadata_doc.get('keywords') if 'keywords' in product.metadata_doc.keys() else [],
        'links': links,
        'extents': {
            'spatial': {
                'bbox': [left, bottom, right, top],
                'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
            }
        },
        'providers': [{
            'type': 'coverage',
            'name': 'odcprovider.OpenDataCubeCoveragesProvider',
            'data': product.name,
            'format': {
                'name': format_name,
                'mimetype': 'application/{}'.format(format_name.lower())
            }
        }],
    }

    return resource_dict


def _merge_config(infile, data):
    """
    Insert auto-created resource entries into given config file if given
    :param infile: file name of a pygeoapi yml config file
    :param data: dict of resource entries
    :return: merged dict of resource entries
    """
    with open(infile, 'r') as infile:
        data_in = yaml.load(infile, Loader=yaml.FullLoader)
        for resource_entry in data['resources']:
            data_in['resources'].update({resource_entry: data['resources'][resource_entry]})
        return data_in


def main():
    args = parse_parameter()

    # Create collection for each datacube product that is not excluded
    dc = OdcConnector()
    data = {'resources': {}}

    products = dc.list_product_names()
    LOGGER.info("Start processing {} products in ODC instance".format(len(products)))
    idx = 1
    for dc_product_name in products:
        LOGGER.info("[{}/{}] Processing product '{}'".format(idx, len(products), dc_product_name))
        if dc_product_name in args.exclude_products:
            LOGGER.info("[{}/{}] Product '{}' is list of products to exclude, hence skipping it"
                        .format(idx, len(products), dc_product_name))
        else:
            LOGGER.info("[{}/{}] Including product '{}'".format(idx, len(products), dc_product_name))
            dc_product = dc.get_product_by_id(dc_product_name)
            format_set = set()
            for dataset in dc.get_datasets_for_product(dc_product.name):
                format_set.add(dataset.format)
            # Make sure bbox is in WGS84
            if len(dc.get_crs_set(dc_product.name)) == 1:
                bbox = convert_datacube_bbox_to_wgs84(dc.bbox_of_product(dc_product.name),
                                                      str(dc.get_crs_set(dc_product.name).pop()))
            else:
                bbox = dc.bbox_of_product(dc_product.name)

            data['resources'][dc_product.name] = _create_resource_from_odc_product(dc_product, bbox, format_set)

        idx = idx + 1

    LOGGER.info("Finished processing {} products".format(len(products)))

    # Write to yaml file, merge with provided config yaml if given
    with open(args.outfile, 'w') as outfile:
        if args.infile is not None:
            data = _merge_config(args.infile, data)
        LOGGER.debug("Writing configuration to file '{}':\n{}\n".format(outfile.name, data))
        yaml.dump(data, outfile, default_flow_style=False, sort_keys=False)

    LOGGER.info("Finished processing ODC products")

if __name__ == "__main__":
    main()
