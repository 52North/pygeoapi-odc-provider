# =================================================================
#
# Authors: Martin Pontius
#
# Copyright (c) 2021 Martin Pontius (52°North)
#
# Add ...
#
# Based on pygeoapi's RasterioProvider (rasterio_.py)
#
# =================================================================


from pygeoapi.provider.base import (BaseProvider, ProviderConnectionError,
                                    ProviderQueryError)

from datacube.utils.geometry import bbox_union

import datacube
from datacube.utils.masking import mask_invalid_data
import math

import logging

LOGGER = logging.getLogger(__name__)


class OpenDataCubeProvider(BaseProvider):
    """OpenDataCube Provider
    This provider plugin maps an OGC collection to an ODC product
    """

    def __init__(self, provider_def):
        """
        Initialize object
        :param provider_def: provider definition
        :returns: pygeoapi.provider.rasterio_.RasterioProvider
        """

        super().__init__(provider_def)

        # ToDo: how to set config files?
        self.dc = datacube.Datacube()
        self.product_name = provider_def['product']
        # self.tags = provider_def['keywords']
        self.tags = "tag"

        try:
            self._coverage_properties = self._get_coverage_properties()
            self.axes = self._coverage_properties['axes']
            self.crs = self._coverage_properties['bbox_crs']
            self.num_bands = self._coverage_properties['num_bands']
            # self.fields = [str(num) for num in range(1, self.num_bands+1)]
        except Exception as err:
            LOGGER.warning(err)
            raise ProviderConnectionError(err)

    def query(self, range_subset=[], subsets={}, bbox=[], datetime_=None,
              format_='json', **kwargs):
        """
        Extract data from collection
        :param range_subset: list of bands
        :param subsets: dict of subset names with lists of ranges
        :param bbox: bounding box [minx,miny,maxx,maxy]
        :param datetime_: temporal (datestamp or extent)
        :param format_: data format of output

        :returns: coverage data as dict of CoverageJSON or native format
        """

        bands = range_subset
        LOGGER.debug('Bands: {}, subsets: {}'.format(bands, subsets))

        minx = 510000.0
        maxx = 515000.0
        miny = 5430000.0
        maxy = 5440000.0

        query = {"x": (minx, maxx),
                 "y": (miny, maxy),
                 "crs": "epsg:2958",
                 "output_crs": "epsg:4326",
                 "align": (0.0005, 0.0005),
                 "resolution": (-0.01, 0.01),
                 "resampling": "nearest"}

        data = self.dc.load(product=self.product_name, **query)

        # Use 'data.time.attrs.pop('units', None)' to prevent the following error:
        # "ValueError: failed to prevent overwriting existing key units in attrs on variable 'time'.
        # This is probably an encoding field used by xarray to describe how a variable is serialized.
        # To proceed, remove this key from the variable's attributes manually."
        data.time.attrs.pop('units', None)

        out_meta = {}
        out_meta['bbox'] = [minx, miny, maxx, maxy]
        out_meta['width'] = 1
        out_meta['height'] = 1

        if format_ == 'json':
            LOGGER.debug('Creating output in CoverageJSON')
            return self.gen_covjson(out_meta, data)

        else:  # return data in native format
            LOGGER.debug('Returning data in native format')
            return data.to_netcdf()

    def gen_covjson(self, metadata, data):
        """
        Generate coverage as CoverageJSON representation
        :param metadata: coverage metadata
        :param data: xarray Dataset object
        :returns: dict of CoverageJSON representation
        """

        LOGGER.debug('Creating CoverageJSON domain')
        minx, miny, maxx, maxy = metadata['bbox']

        cj = {
            'type': 'Coverage',
            'domain': {
                'type': 'Domain',
                'domainType': 'Grid',
                'axes': {
                    'x': {
                        'start': minx,
                        'stop': maxx,
                        'num': metadata['width']
                    },
                    'y': {
                        'start': maxy,
                        'stop': miny,
                        'num': metadata['height']
                    }
                },
                'referencing': [{
                    'coordinates': ['x', 'y'],
                    'system': {
                        'type': self._coverage_properties['crs_type'],
                        'id': self._coverage_properties['bbox_crs']
                    }
                }]
            },
            'parameters': {},
            'ranges': {}
        }

        # ToDo: implement band selection and parameters correctly

        bands_select = 'dsm'

        LOGGER.debug('bands selected: {}'.format(bands_select))
        for bs in bands_select:

            parameter = {
                'type': 'Parameter',
                'description': 'dsm',
                'unit': {
                    'symbol': 'm'
                },
                'observedProperty': {
                    'id': 'dsm',
                    'label': {
                        'en': 'dsm'
                    }
                }
            }

            cj['parameters']['dsm'] = parameter

        try:
            for key in cj['parameters'].keys():
                cj['ranges'][key] = {
                    'type': 'NdArray',
                    # 'dataType': metadata.dtypes[0],
                    'dataType': 'float',
                    'axisNames': ['y', 'x'],
                    'shape': [metadata['height'], metadata['width']],
                }
                cj['ranges'][key]['values'] = data['dsm'].values.flatten().tolist()
        except IndexError as err:
            LOGGER.warning(err)
            raise ProviderQueryError('Invalid query parameter')

        return cj

    def get_coverage_domainset(self):
        """
         Provide coverage domainset
         :returns: CIS JSON object of domainset metadata
         """

        domainset = {
            'type': 'DomainSetType',
            'generalGrid': {
                'type': 'GeneralGridCoverageType',
                'srsName': self._coverage_properties['bbox_crs'],
                'axisLabels': [
                    self._coverage_properties['x_axis_label'],
                    self._coverage_properties['y_axis_label']
                ],
                'axis': [{
                    'type': 'RegularAxisType',
                    'axisLabel': self._coverage_properties['x_axis_label'],
                    'lowerBound': self._coverage_properties['bbox'][0],
                    'upperBound': self._coverage_properties['bbox'][2],
                    'uomLabel': self._coverage_properties['bbox_units'],
                    'resolution': self._coverage_properties['resx']
                }, {
                    'type': 'RegularAxisType',
                    'axisLabel': self._coverage_properties['y_axis_label'],
                    'lowerBound': self._coverage_properties['bbox'][1],
                    'upperBound': self._coverage_properties['bbox'][3],
                    'uomLabel': self._coverage_properties['bbox_units'],
                    'resolution': self._coverage_properties['resy']
                }],
                'gridLimits': {
                    'type': 'GridLimitsType',
                    'srsName': 'http://www.opengis.net/def/crs/OGC/0/Index2D',
                    'axisLabels': ['i', 'j'],
                    'axis': [{
                        'type': 'IndexAxisType',
                        'axisLabel': 'i',
                        'lowerBound': 0,
                        'upperBound': self._coverage_properties['width']
                    }, {
                        'type': 'IndexAxisType',
                        'axisLabel': 'j',
                        'lowerBound': 0,
                        'upperBound': self._coverage_properties['height']
                    }]
                }
            },
            '_meta': {
                'tags': self._coverage_properties['tags']
            }
        }

        return domainset

    def get_coverage_rangetype(self):
        """
        Provide coverage rangetype
        :returns: CIS JSON object of rangetype metadata
        """

        measurement_list = self.dc.list_measurements()
        measurement_metadata = measurement_list.loc[self.product_name]

        fields = []
        for row in range(0, len(measurement_metadata)):
            fields.append({
                "id": row + 1,
                "type": "QuantityType",
                "name": measurement_metadata.iloc[row]['name'],
                "definition": measurement_metadata.iloc[row]['dtype'],
                "nodata": measurement_metadata.iloc[row]['nodata'].item(),
                "uom": {
                    "id": "http://www.opengis.net/def/uom/UCUM/[C]",
                    "type": "UnitReference",
                    "code": measurement_metadata.iloc[row]['units']
                },
                "_meta": {
                    "tags": {
                        "Aliases": measurement_metadata.iloc[row]['aliases'],
                    }
                }
            })

        rangetype = {
            "type": "DataRecordType",
            "field": fields
        }

        return rangetype

    def _get_coverage_properties(self):
        """
        Helper function to normalize coverage properties
        :returns: `dict` of coverage properties
        """

        # Most metadata is specified on dataset level, not on product level
        # product_list = self.dc.list_products()
        # product_metadata = product_list[product_list['name'] == self.product_name]

        # Resolution (metadata field is optional on product level)
        # res = product_metadata.iloc[0]['resolution']
        # if isinstance(res, tuple):
        #     # ToDO: check coordinate order
        #     resx = res[0]
        #     resy = res[1]
        # else:
        #     resx = None
        #     resy = None

        # Harvest metadata from odc datasets of the specified product

        bbs = []
        crs_list = []
        resx_list = []
        resy_list = []
        for dataset in self.dc.find_datasets(product=self.product_name):
            bbs.append(dataset.bounds)
            crs_list.append(dataset.crs)
            resx_list.append(dataset.__dict__['metadata_doc']['grids']['default']['transform'][0])
            resy_list.append(dataset.__dict__['metadata_doc']['grids']['default']['transform'][4])

        bounds = bbox_union(bbs)

        if len(set(crs_list)) > 1:
            LOGGER.warning("Product {} has datasets with different coordinate reference systems. First crs found is "
                           "shown in domainset.".format(self.product_name))
        crs = crs_list[0]

        if len(set(resx_list)) > 1 or len(set(resy_list)) > 1:
            LOGGER.warning("Product {} has datasets with different spatial resolution. First resolution found is "
                           "shown in domainset.".format(self.product_name))
        resx = resx_list[0]
        resy = resy_list[0]

        properties = {
            'bbox': [
                bounds.left,
                bounds.bottom,
                bounds.right,
                bounds.top
            ],
            'bbox_crs': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84',
            'crs_type': 'GeographicCRS',
            'bbox_units': 'deg',
            'x_axis_label': 'Long',
            'y_axis_label': 'Lat',
            'width': bounds.right - bounds.left,
            'height': bounds.top - bounds.bottom,
            'resx': resx,
            'resy': resy,
            'num_bands': len(self.dc.index.products.get_by_name(self.product_name).measurements),
            'tags': self.tags
        }

        if crs.projected:
            properties['bbox_crs'] = '{}/{}'.format('http://www.opengis.net/def/crs/EPSG/9.8.15', crs.to_epsg())
            properties['x_axis_label'] = 'x'
            properties['y_axis_label'] = 'y'
            properties['bbox_units'] = crs.units[0]
            properties['crs_type'] = 'ProjectedCRS'

        properties['axes'] = [
            properties['x_axis_label'], properties['y_axis_label']
        ]

        return properties
