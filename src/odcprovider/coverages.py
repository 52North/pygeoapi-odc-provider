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
# Based on pygeoapi's RasterioProvider
# https://github.com/geopython/pygeoapi/blob/master/pygeoapi/provider/rasterio_.py
#
# =================================================================

import logging
import json
# ToDo move to OdcConnector somehow
from datacube.utils.geometry import CRS as CRS_DATACUBE, BoundingBox
from pandas import isnull
from pygeoapi.provider.base import (BaseProvider,
                                    ProviderConnectionError,
                                    ProviderGenericError,
                                    ProviderQueryError)
from pyproj import CRS, Transformer
from rasterio import Affine
from rasterio.io import MemoryFile

from .connector import OdcConnector

import numpy as np

LOGGER = logging.getLogger(__name__)


class OpenDataCubeCoveragesProvider(BaseProvider):
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

        self.dc = OdcConnector()

        products = self.dc.list_product_names()

        if self.data not in products:
            raise ProviderGenericError("Configured product '{}' is not contained in OpenDataCube instance"
                                       .format(self.data))

        LOGGER.info('Start initializing product {}'.format(self.data))

        try:
            self.crs_obj = None  # datacube.utils.geometry.CRS
            bbox = self._get_bbox()  # datacube.utils.geometry.BoundingBox
            self._coverage_properties = self._get_coverage_properties(bbox)
            self._measurement_properties = self._get_measurement_properties()
            self.native_format = provider_def['format']['name']
            # axes, crs and num_bands is need for coverage providers (see https://github.com/geopython/pygeoapi/blob/master/pygeoapi/provider/base.py#L65)
            self.axes = self._coverage_properties['axes']
            self.crs = self._coverage_properties['crs_uri']
            self.num_bands = self._coverage_properties['num_bands']
            self.fields = [str(num) for num in range(1, self.num_bands + 1)]
            LOGGER.info('Finished initializing product {}'.format(self.data))
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
        # ---------------- #
        # Query parameters (https://ogcapi.ogc.org/coverages/overview.html)
        # url: {datasetAPI}/collections/{coverageid}/coverage
        # Subset with well-defined ranges for named axes
        # ?subset=Lat(40:50),Lon(10: 20)
        # ?subset=time("2019-03-27")
        # Band subset
        # ?rangeSubset=B02,B03,B04
        # Bbox (in WGS84 or WGS84h)
        # ?bbox=10,40,20,50
        # Scaling
        # ?scaleSize=Lon(800),Lat(400)
        # ?scaleFactor=2
        # ?scaleAxes=Lon(2)
        # ---------------- #

        bands = range_subset
        LOGGER.info('Bands: {}, subsets: {}'.format(bands, subsets))

        # initial bbox, full extent of collection
        minx, miny, maxx, maxy = self._coverage_properties['bbox']

        if all([not bands, not subsets, not bbox]):
            LOGGER.info('No parameters specified')

        if all([self._coverage_properties['x_axis_label'] not in subsets,
                self._coverage_properties['y_axis_label'] not in subsets,
                not bbox]):
            msg = 'spatial subsetting via bbox parameter or subset is mandatory'
            LOGGER.warning(msg)
            raise ProviderQueryError(msg)

        if all([self._coverage_properties['x_axis_label'] in subsets,
                self._coverage_properties['y_axis_label'] in subsets,
                len(bbox) > 0]):
            msg = 'bbox and subsetting by coordinates are exclusive'
            LOGGER.warning(msg)
            raise ProviderQueryError(msg)

        # -------------- #
        # Spatial subset #
        # -------------- #
        if len(bbox) > 0:
            minxbox, minybox, maxxbox, maxybox = bbox

            # fixed by specification
            crs_src = CRS.from_epsg(4326)
            crs_dest = CRS.from_epsg(self.crs_obj.to_epsg())

            if crs_src == crs_dest:
                LOGGER.info('source bbox CRS and data CRS are the same')
            else:
                LOGGER.info('source bbox CRS and data CRS are different')
                LOGGER.info('reprojecting bbox into native coordinates')

                t = Transformer.from_crs(crs_src, crs_dest, always_xy=True)
                minx, miny = t.transform(minxbox, minybox)
                maxx, maxy = t.transform(maxxbox, maxybox)

                LOGGER.info('Source coordinates: {}'.format(
                    [minxbox, minybox, maxxbox, maxybox]))
                LOGGER.info('Destination coordinates: {}'.format(
                    [minx, miny, maxx, maxy]))

        elif (self._coverage_properties['x_axis_label'] in subsets and
                self._coverage_properties['y_axis_label'] in subsets):
            LOGGER.info('Creating spatial subset')

            x = self._coverage_properties['x_axis_label']
            y = self._coverage_properties['y_axis_label']

            minx = subsets[x][0]
            maxx = subsets[x][1]
            miny = subsets[y][0]
            maxy = subsets[y][1]

        # ToDo consider resolution in next development iteration

        if minx > maxx or miny > maxy:
            msg = 'spatial subsetting invalid min > max'
            LOGGER.warning(msg)
            raise ProviderQueryError(msg)

        if self.data != 'landsat8_c2_l2':
            if self.crs_obj.projected:
                max_allowed_delta = 7500
            else:
                max_allowed_delta = 0.125

            if maxx - minx > max_allowed_delta:
                msg = 'spatial subsetting to large {}. please request max {}'.format(maxx - minx, max_allowed_delta)
                LOGGER.warning(msg)
                raise ProviderQueryError(msg)

            if maxy - miny > max_allowed_delta:
                msg = 'spatial subsetting to large {}. please request max {}'.format(maxy - miny, max_allowed_delta)
                LOGGER.warning(msg)
                raise ProviderQueryError(msg)

        # ------------------------------ #
        # Parameters for datacube.load() #
        # ------------------------------ #

        # Note: resolution and align expect the following coordinate order: (y, x)
        # Note: datacube.Datacube.load accepts all of the following parameters for spatial subsets
        #       independent of the crs: 'latitude' or 'lat' or 'y' / 'longitude' or 'lon' or 'long' or 'x'
        params = {
            "crs": "epsg:{}".format(self.crs_obj.to_epsg()),
            "align": (abs(self._coverage_properties['resy'] / 2),
                      abs(self._coverage_properties['resx'] / 2)),
            # in the units of output_crs (if output_crs is not supplied, crs of stored data is used)
            'x': (minx, maxx),
            'y': (miny, maxy),
        }

        if len(bands) > 0:
            params['measurements'] = bands

        # ToDo: enable output in different crs? Does API Coverages support this?
        # ToDo: check if re-projection is necessary
        # ToDo: if product has more than one crs, output crs should be in WGS84!?
        if self.dc.get_product_by_id(self.data).grid_spec is None:
            params['resolution'] = (self._coverage_properties['resy'], self._coverage_properties['resx'])
            params['output_crs'] = "epsg:4326"
            # resampling := 'nearest' is the default value
            # params['resampling'] = 'nearest'

        LOGGER.debug('RAW params for dc.load:\n{}'.format(json.dumps(params, indent=4)))
        # ---------------------- #
        # Load data via datacube #
        # ---------------------- #
        #
        # See https://datacube-core.readthedocs.io/en/latest/dev/api/generate/datacube.Datacube.load.html
        #
        dataset = self.dc.load(product=self.data, **params)
        LOGGER.debug('Received data from ODC')

        # Use 'dataset.time.attrs.pop('units', None)' to prevent the following error:
        # "ValueError: failed to prevent overwriting existing key units in attrs on variable 'time'.
        # This is probably an encoding field used by xarray to describe how a variable is serialized.
        # To proceed, remove this key from the variable's attributes manually."
        # Check for existence to "prevent AttributeError: 'Dataset' object has no attribute 'time'"
        if hasattr(dataset, 'time') and dataset.time is not None and hasattr(dataset.time, 'attrs') and \
                dataset.time.attrs is not None:
            dataset.time.attrs.pop('units', None)

        # ------------------------------------- #
        # Return coverage json or native format #
        # ------------------------------------- #
        if len(bands) == 0:
            bands = list(dataset.keys())  # select all bands

        out_meta = {
            'bbox': [minx, miny, maxx, maxy],
            'width': abs((maxx - minx) / self._coverage_properties['resx']),
            'height': abs((maxy - miny) / self._coverage_properties['resy']),
            'bands': bands
        }

        if self.options is not None:
            LOGGER.info('Adding dataset options')
            for key, value in self.options.items():
                out_meta[key] = value

        LOGGER.debug('Processed dataset')

        if format_ == 'json':
            LOGGER.info('Creating output in CoverageJSON')
            return self.gen_covjson(out_meta, dataset)

        elif format_.lower() == 'geotiff':
            LOGGER.info('Returning data as GeoTIFF')
            # ToDo: check if there is more than one time slice
            out_meta['driver'] = 'GTiff'
            out_meta['crs'] = self.crs_obj.to_epsg()
            out_meta['dtype'] = self._measurement_properties[0]['dtype']
            out_meta['nodata'] = self._measurement_properties[0]['nodata']
            out_meta['count'] = len(bands)
            # ToDo: Coordinates seem to be shifted by resolution/2
            out_meta['transform'] = Affine(self._coverage_properties['transform'][0],
                                           self._coverage_properties['transform'][1],
                                           self._coverage_properties['transform'][2],
                                           self._coverage_properties['transform'][3],
                                           self._coverage_properties['transform'][4],
                                           self._coverage_properties['transform'][5])
            LOGGER.debug('Writing to in-memory file')
            with MemoryFile() as memfile:
                with memfile.open(**out_meta) as dest:
                    # input is expected as (bands, rows, cols)
                    dest.write(np.stack([dataset.squeeze(dim='time', drop=True)[bs].values for bs in bands], axis=0))
                LOGGER.debug('Finished writing to in-memory file')
                return memfile.read()

        else:
            LOGGER.info('Returning data as netCDF')
            # Note: "If no path is provided, this function returns the resulting netCDF file as bytes; in this case,
            # we need to use scipy, which does not support netCDF version 4 (the default format becomes NETCDF3_64BIT)."
            # (http://xarray.pydata.org/en/stable/generated/xarray.Dataset.to_netcdf.html)
            return dataset.to_netcdf()

    def gen_covjson(self, metadata, dataset):
        """
        Generate coverage as CoverageJSON representation
        :param metadata: coverage metadata
        :param dataset: xarray Dataset object
        :returns: dict of CoverageJSON representation
        """

        # ToDo: support time dimension

        LOGGER.info('Creating CoverageJSON domain')
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
                        'start': miny,
                        'stop': maxy,
                        'num': metadata['height']
                    }
                },
                'referencing': [{
                    'coordinates': ['x', 'y'],
                    'system': {
                        'type': self._coverage_properties['crs_type'],
                        'id': self._coverage_properties['crs_uri']
                    }
                }]
            },
            'parameters': {},
            'ranges': {}
        }

        bands_select = metadata['bands']

        LOGGER.info('bands selected: {}'.format(bands_select))
        for bs in bands_select:

            parameter = {
                'type': 'Parameter',
                'description': bs,
                'unit': {
                    'symbol': dataset[bs].attrs['units']
                },
                'observedProperty': {
                    'id': bs,
                    'label': {
                        'en': bs
                    }
                }
            }

            cj['parameters'][bs] = parameter

        # ToDo: check shape/axis order!
        try:
            for key in cj['parameters'].keys():
                cj['ranges'][key] = {
                    'type': 'NdArray',
                    'dataType': str(dataset[key].dtype),
                    'axisNames': ['y', 'x'],
                    'shape': [metadata['height'], metadata['width']],
                }
                cj['ranges'][key]['values'] = dataset[key].values.flatten().tolist()
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
                'srsName': self._coverage_properties['crs_uri'],
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
            # '_meta': {
            #     'tags': self._coverage_properties['tags']
            # }
        }

        return domainset

    def get_coverage_rangetype(self):
        """
        Provide coverage rangetype
        :returns: CIS JSON object of rangetype metadata
        """

        fields = []
        for row in range(0, len(self._measurement_properties)):
            fields.append({
                "id": self._measurement_properties[row]['id'],
                "type": "QuantityType",
                "name": self._measurement_properties[row]['name'],
                "definition": self._measurement_properties[row]['dtype'],
                "nodata": self._measurement_properties[row]['nodata'],
                "uom": {
                    # "id": "http://www.opengis.net/def/uom/UCUM/[C]", # ToDo: get correct uri for arbitrary units
                    "type": "UnitReference",
                    "code": self._measurement_properties[row]['unit']
                },
                "_meta": {
                    "tags": {
                        "Aliases": self._measurement_properties[row]['aliases']
                        if self._measurement_properties[row]['aliases'] is not None else "NaN",
                    }
                }
            })

        rangetype = {
            "type": "DataRecordType",
            "field": fields
        }

        return rangetype

    def _get_bbox(self) -> BoundingBox:
        bbox = self.dc.bbox_of_product(self.data)
        LOGGER.info('bbox of product {}: {}'.format(self.data, bbox))
        return bbox

    def _get_coverage_properties(self, bbox: BoundingBox) -> dict:
        """
        Helper function to normalize coverage properties
        :returns: `dict` of coverage properties
        """

        # Note:
        # - Some metadata are specified on product level and some on dataset level or even on both (e.g. crs)
        # - Some (product) metadata are optional, thus they may not be available for all products
        # - Different datasets for the same product may have different crs

        # ---------------- #
        # Product metadata #
        # ---------------- #
        # With datacube versions > 1.8.3, metadata can alternatively be obtained like this:
        # self.dc.index.products.get_by_name(self.product_name).default_crs
        # https://datacube-core.readthedocs.io/en/latest/dev/api/generate/datacube.model.DatasetType.html#datacube.model.DatasetType

        product_metadata = self.dc.get_product_by_id(self.data)

        if product_metadata is None:
            raise RuntimeError("Could not retrieve product '{}'".format(self.data))

        res = None
        crs_str = None

        if 'storage' in product_metadata.definition.keys() and \
                'resolution' in product_metadata.definition.get('storage').keys():
            res = product_metadata.definition.get('storage').get('resolution')

            if 'crs' in product_metadata.definition.get('storage').keys():
                crs_str = str(product_metadata.definition.get('storage').get('crs'))

        if res is not None:
            if isinstance(res, tuple):
                # ToDo: check coordinate order!
                resx = res[1]
                resy = res[0]
            elif isinstance(res, dict) and 'x' in res.keys() and 'y' in res.keys():
                resx = res.get('x')
                resy = res.get('y')
        else:
            resx = None
            resy = None

        # spatial_dimensions = product_metadata.iloc[0]['spatial_dimensions']
        # if isinstance(spatial_dimensions, tuple):
        #     # ToDo: check axis order!
        #     dim_we = spatial_dimensions[1]
        #     dim_ns = spatial_dimensions[0]
        # else:
        #     dim_we = None
        #     dim_ns = None

        num_bands = self.dc.number_of_bands(self.data)

        # ---------------- #
        # Dataset metadata #
        # ---------------- #
        crs_list = []
        resx_list = []
        resy_list = []
        transform_list = []
        dim_list = []
        # ToDo can we replace this for-loop by using OdcConnector.bbox_of_product()?
        for dataset in self.dc.get_datasets_for_product(self.data):
            crs_list.append(dataset.crs)
            # ToDo: check coordinate order!
            resx_list.append(dataset.metadata_doc['grids']['default']['transform'][0])
            resy_list.append(dataset.metadata_doc['grids']['default']['transform'][4])
            transform_list.append(dataset.metadata_doc['grids']['default']['transform'])
            dim_list.append(dataset.crs.dimensions)

        # Check if all datasets have the same crs, resolution and transform
        if len(set(crs_list)) > 1:
            LOGGER.warning("Product {} has datasets with different coordinate reference systems.".format(self.data))
        if len(set(resx_list)) > 1 or len(set(resy_list)) > 1:
            LOGGER.warning("Product {} has datasets with different spatial resolutions.".format(self.data))
        if len(set(tuple(i) for i in transform_list)) > 1:
            LOGGER.warning("Product {} has datasets with different transforms.".format(self.data))

        # Use dataset metadata if metadata was not specified on product level
        # ToDo: support different crs/resolution for different datasets including reprojection
        if crs_str is None or isnull(crs_str):
            self.crs_obj = crs_list[0]
        else:
            self.crs_obj = CRS_DATACUBE(crs_str)

        if resx is None:
            resx = resx_list[0]
        if resy is None:
            resy = resy_list[0]

        transform = transform_list[0]

        # if dim_we is None:
        #     dim_we = dim_list[1]
        # if dim_ns is None:
        #     dim_ns = dim_list[0]

        # -------------- #
        # Set properties #
        # -------------- #
        properties = {
            'bbox': [
                bbox.left,
                bbox.bottom,
                bbox.right,
                bbox.top
            ],
            'crs_uri': 'http://www.opengis.net/def/crs/OGC/1.3/CRS84',
            'crs_type': 'GeographicCRS',
            'bbox_units': 'deg',
            'x_axis_label': 'Lon',
            'y_axis_label': 'Lat',
            'width': abs((bbox.right - bbox.left) / resx),
            'height': abs((bbox.top - bbox.bottom) / resy),
            'resx': resx,
            'resy': resy,
            'transform': transform,
            'num_bands': num_bands,
            # 'tags': 'tags'
        }

        if self.crs_obj.projected:
            properties['crs_uri'] = 'http://www.opengis.net/def/crs/EPSG/9.8.15/{}'.format(self.crs_obj.to_epsg())
            properties['x_axis_label'] = 'x'
            properties['y_axis_label'] = 'y'
            properties['bbox_units'] = self.crs_obj.units[0]
            properties['crs_type'] = 'ProjectedCRS'

        properties['axes'] = [
            properties['x_axis_label'], properties['y_axis_label']
        ]

        return properties

    def _get_measurement_properties(self):
        """
        Helper function to normalize measurement properties
        :returns: `dict` of measurement properties
        """

        measurement_list = self.dc.list_measurements()
        measurement_metadata = measurement_list.loc[self.data]

        properties = []
        for row in range(0, len(measurement_metadata)):
            properties.append({
                "id": row + 1,
                "name": measurement_metadata.iloc[row]['name'],
                "dtype": measurement_metadata.iloc[row]['dtype'],
                "nodata": measurement_metadata.iloc[row]['nodata'],
                "unit": measurement_metadata.iloc[row]['units'],
                "aliases": measurement_metadata.iloc[row]['aliases']
                if 'aliases' in measurement_metadata.columns else "None",
            })

        return properties
