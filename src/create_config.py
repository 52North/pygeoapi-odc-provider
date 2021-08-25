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
import yaml
import argparse
from odcprovider.connector import OdcConnector
from odcprovider.utils import convert_datacube_bbox_to_wgs84

# datacube products to be exlcuded from pygeoapi
EXCLUDED_PRODUCTS = ['minimal_example_eo', 'minimal_example_eo3', 'landsat8_c2_l2']

# list of links which are not available in datacube metadata
LINKS = {
    'nrcan_dsm':
        {
            'title': 'High Resolution Digital Elevation Model (HRDEM) - CanElevation Series',
            'href': 'https://open.canada.ca/data/en/dataset/957782bf-847c-4644-a757-e383c0057995'
        },
}


# ToDo: improve formatting

def parse_parameter() -> argparse.Namespace:
    # argument parser, takes two optional comment line arguments (input and output file name)
    # ToDo: is it better to use type=argparse.FileType('w') or type=argparse.FileType('r') instead of default str?
    parser = argparse.ArgumentParser(
        description='Create resource entries for pygeoapi configuration. If infile is '
                    'provided, resource entries will be inserted there and written to outfile.')
    parser.add_argument('--infile', '-i',
                        help='File name of the config yaml that should be merged.')
    parser.add_argument('--outfile', '-o',
                        default='config_auto.yml',
                        help='Output yaml file name (default: config_auto.yml)')
    return parser.parse_args()


def _create_resource_from_odc_product(dc, product):
    """
    Create resource from Open Data CUbe product

    :param dc: ODC connector
    :param product: ODC product
    :return: dict
    """

    # ToDo: what if products do not have crs?
    left, bottom, right, top = convert_datacube_bbox_to_wgs84(dc.bbox_of_product(product['name']), product['crs'])
    if product['format'] is not None:
        format_name = product['format']
    else:
        format_name = 'NetCDF'

    resource_dict = {
        'type': 'collection',
        'title': product['name'],
        'description': product['description'],
        'keywords': ['dsm', 'Canada', 'MB', 'The Pas 2014'],  # ToDo: generalize
        'links': [{
            'type': 'text/html',
            'rel': 'canonical',
            'title': LINKS['nrcan_dsm']['title'],  # ToDo: generalize
            'href': LINKS['nrcan_dsm']['href'],  # ToDo: generalize
            'hreflang': 'en-US'
        }],
        'extents': {
            'spatial': {
                'bbox': [left, bottom, right, top],
                'crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84'
            }
        },
        'providers': [{
            'type': 'coverage',
            'name': 'odcprovider.OpenDataCubeCoveragesProvider',
            'data': product['name'],
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
    :param infile:
    :param data:
    :return:
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
    for dc_product in dc.list_products(with_pandas=False):
        if dc_product['name'] not in EXCLUDED_PRODUCTS:
            data['resources'][dc_product['name']] = _create_resource_from_odc_product(dc, dc_product)

    # Write to yaml file, merge with provided config yaml if given
    with open(args.outfile, 'w') as outfile:
        if args.infile is not None:
            data = _merge_config(args.infile, data)
        yaml.dump(data, outfile, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    main()
