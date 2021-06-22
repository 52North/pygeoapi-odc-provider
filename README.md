# pygeoapi-odc-provider

Provider plugin for pygeoapi to include Open Data Cube as a data resource.

Install: `python setup.py install`

A new collection can be added to the pygeoapi config.yaml with the following provider section after this library was installed:

```
providers:
  - type: coverage
    name: odcprovider.OpenDataCubeProvider
    data: ~/.datacube.conf   # not used at the moment
    product: <product_name>
    format:
        name: NetCDF
        mimetype: application/netcdf
```
