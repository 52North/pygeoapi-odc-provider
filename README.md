# pygeoapi-odc-provider

Provider plugin for pygeoapi to include Open Data Cube as a data resource.

A new collection can be added to the pygeoapi config.yaml with the following provider section:

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
