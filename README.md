# pygeoapi-odc-provider

Provider plugin for pygeoapi to include Open Data Cube as a data resource.

Install: `python setup.py install` or `python -m pip install .`

A new collection can be added to the pygeoapi config.yaml with the following provider section after this library was installed:

```yaml
providers:
  - type: coverage
    name: odcprovider.OpenDataCubeCoveragesProvider
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
        name: odcprovider.HelloWorldProcessor
```

Use the following curl call for testing the process:

```sh
curl -i -s -H "Content-Type: application/json" -X POST -d @request.json 'https://17.testbed.dev.52north.org/geodatacube/processes/hello-world/execution'
```

with `request.json`:

```json
{
   "inputs": {
      "name": "Mr Test McTestface",
      "message": "Your are so testy today!"
   }
}
```

## Changelog

* **0.2.0**: add first processors
* **0.0.1**: init with coverages provider

## ToDos

* [ ] Clarify License: MIT vs GPLv2 vs Apache 2.0 for service libs @52N
