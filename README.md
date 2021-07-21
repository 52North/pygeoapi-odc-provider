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


Add new process can be configured by adding the following to the `config.yaml`:

```yaml
[...]
  resources:
      hello-world:
      type: process
      processor:
        name: odcprovider.OpenDataCubeProviderProcesses
```

Use the following curl call for testing the process:

```sh
curl -i -s -H "Content-Type: application/json" -X POST -d @request.json 'https://17.testbed.dev.52north.org/geodatacube/processes/hello-world/jobs'
```

with `request.json`:

```json
{
   "inputs": [
      {
         "id": "name",
         "value": "Mr Test McTestface",
         "type": "text/plain"
      },
      {
         "id": "message",
         "value": "Your are so testy today!",
         "type": "text/plain"
      }
   ]
}
```