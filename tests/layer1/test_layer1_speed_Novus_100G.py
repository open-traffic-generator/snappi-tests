import pytest

@pytest.mark.non_uhd
def test_layer1(api, utils):
    """Test that layer1 configuration settings are being applied correctly
    A user should be able to configure ports with/without locations.
    The expectation should be if a location is configured the user wants to
    connect but debug should allow for config creation without location.
    Ports with no location should not generate an error message.
    Ports with location should generate an error message if unable to connect.

    Validation: Validate the layer1 properties applied using Restpy
    """
    config = api.config()
    port = config.ports.port(name="port1", location=utils.settings.ports[0])[
        -1
    ]
    ieee_media_defaults = False
    auto_negotiate = True
    link_training = True
    rs_fec = True

    layer1 = config.layer1.layer1()[-1]
    layer1.name = "port1 settings"
    layer1.port_names = [port.name]
    layer1.speed = "speed_100_gbps"
    layer1.ieee_media_defaults = ieee_media_defaults
    layer1.auto_negotiate = auto_negotiate
    layer1.auto_negotiation.link_training = link_training
    layer1.auto_negotiation.rs_fec = rs_fec

    api.set_config(config)
    validate_layer1_config(
        api,
        auto_negotiate,
        ieee_media_defaults,
        link_training,
        rs_fec,
    )


def validate_layer1_config(
    api,
    auto_negotiate,
    ieee_media_defaults,
    link_training,
    rs_fec,
):
    """
    Validate Layer1 Configs using Restpy
    """
    ixnetwork = api._ixnetwork
    port = ixnetwork.Vport.find()[0]
    type = (port.Type)[0].upper() + (port.Type)[1:]
    assert port.ActualSpeed == 100000
    assert getattr(port.L1Config, type).IeeeL1Defaults == ieee_media_defaults
    assert getattr(port.L1Config, type).EnableAutoNegotiation == auto_negotiate
    assert getattr(port.L1Config, type).EnableRsFec == rs_fec
    assert getattr(port.L1Config, type).LinkTraining == link_training
