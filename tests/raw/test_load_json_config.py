import pytest


@pytest.mark.parametrize('jsonfile', ['configs_list_tcp_ports.json'])
def test_json_load_config(api, utils, jsonfile):
    """
    loads the json file from the configs path
    """
    config = api.config()
    jsonfile = utils.get_test_config_path(jsonfile)
    with open(jsonfile, 'r') as fd:
        config.deserialize(fd.read())
    config.ports[0].location = "10.39.65.230;5;1"
    config.ports[1].location = "10.39.65.230;5;2"
    ports = []
    ports.append({
        "name": config.ports[0].name,
        "location": "10.39.65.230;5;1"
    })
    ports.append({
        "name": config.ports[1].name,
        "location": "10.39.65.230;5;2"
    })

    assert ports == config.ports.serialize('dict')
    api.set_config(config)
