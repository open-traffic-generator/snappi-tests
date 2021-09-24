
tx_port_name := "p1"
rx_port_name := "p2"
flow_name := "f1"
macAddr1 := "00:15:00:00:00:01"
macAddr2 := "00:16:00:00:00:01"
mtu := 1500

ipAddress1 := "20.20.20.1"
ipGateway1 := "20.20.20.2"
ipAddress2 := "30.30.30.1"
ipGateway2 := "30.30.30.2"
ipPrefix := 24

bgpLocalAddress1 := "20.20.20.1"
bgpDutAddress1 := "20.20.20.2"
bgpRouterId1 := "20.20.20.1"
bgpLocalAddress2 := "30.30.30.1"
bgpDutAddress2 := "30.30.30.2"
bgpRouterId2 := "30.30.30.1"
bgpActive := true
bgpAsType := "ebgp"
bgpAsNumber := 3001
nextHopAddress1 := "20.20.20.1"
routeAddress1 := "11.11.11.1"
nextHopAddress2 := "30.30.30.1"
routeAddress2 := "12.12.12.1"
routeCount := "2"
routeStep := "0.0.1.0"
routePrefix := 24

// Test config setup
duration_type := "fixed_packets"
rate_type := "pps"
packets := 10000
pps := 1000
src_mac := macAddr1
src_mac2 := macAddr2
dst_mac1 := "a2:71:d4:59:b3:b8"
dst_mac2 := "6e:d2:47:65:aa:69"
dst_ip := routeAddress2
src_ip := routeAddress1

eth_dst := otgclient.PatternFlowEthernetDst{Choice: "value", Value: &dst_mac1}
eth_src := otgclient.PatternFlowEthernetSrc{Choice: "value", Value: &src_mac}
pkt_ethernet := otgclient.FlowEthernet{Dst: &eth_dst, Src: &eth_src}
ip_dst := otgclient.PatternFlowIpv4Dst{Choice: "value", Value: &dst_ip}
ip_src := otgclient.PatternFlowIpv4Src{Choice: "value", Value: &src_ip}
pkt_ipv4 := otgclient.FlowIpv4{Dst: &ip_dst, Src: &ip_src}

eth_dst2 := otgclient.PatternFlowEthernetDst{Choice: "value", Value: &dst_mac2}
eth_src2 := otgclient.PatternFlowEthernetSrc{Choice: "value", Value: &src_mac2}
pkt2_ethernet := otgclient.FlowEthernet{Dst: &eth_dst2, Src: &eth_src2}
ip_dst2 := otgclient.PatternFlowIpv4Dst{Choice: "value", Value: &src_ip}
ip_src2 := otgclient.PatternFlowIpv4Src{Choice: "value", Value: &dst_ip}
pkt2_ipv4 := otgclient.FlowIpv4{Dst: &ip_dst2, Src: &ip_src2}

resp, err := client.SetConfigWithResponse(ctx, otgclient.SetConfigJSONRequestBody{
    Flows: &[]otgclient.Flow{{
        Duration: &otgclient.FlowDuration{
            Choice: duration_type,
            FixedPackets: &otgclient.FlowFixedPackets{
                Packets: &packets,
            },
        },
        Rate: &otgclient.FlowRate{
            Choice: rate_type,
            Pps:    &pps,
        },
        Name: "f1",
        Packet: &[]otgclient.FlowHeader{
            otgclient.FlowHeader{
                Choice:   "ethernet",
                Ethernet: &pkt_ethernet,
            },
            otgclient.FlowHeader{
                Choice: "ipv4",
                Ipv4:   &pkt_ipv4,
            },
        },
        TxRx: otgclient.FlowTxRx{
            Choice: "port",
            Port: &otgclient.FlowPort{
                TxName: tx_port_name,
                RxName: &rx_port_name,
            },
        },
    }, {
        Duration: &otgclient.FlowDuration{
            Choice: duration_type,
            FixedPackets: &otgclient.FlowFixedPackets{
                Packets: &packets,
            },
        },
        Rate: &otgclient.FlowRate{
            Choice: rate_type,
            Pps:    &pps,
        },
        Name: "f2",
        Packet: &[]otgclient.FlowHeader{
            otgclient.FlowHeader{
                Choice:   "ethernet",
                Ethernet: &pkt2_ethernet,
            },
            otgclient.FlowHeader{
                Choice: "ipv4",
                Ipv4:   &pkt2_ipv4,
            },
        },
        TxRx: otgclient.FlowTxRx{
            Choice: "port",
            Port: &otgclient.FlowPort{
                TxName: rx_port_name,
                RxName: &tx_port_name,
            },
        },
    }},
    Ports: &[]otgclient.Port{
        otgclient.Port{
            Location: &configMap[0].node.reference,
            Name:     tx_port_name,
        },
        otgclient.Port{
            Location: &configMap[1].node.reference,
            Name:     rx_port_name,
        },
    },
    Devices: &[]otgclient.Device{
        {
            Name:          "DeviceGroup1",
            ContainerName: tx_port_name,
            Ethernet: otgclient.DeviceEthernet{
                Name: "Ethernet1",
                Mac:  &macAddr1,
                Mtu:  &mtu,
                Ipv4: &otgclient.DeviceIpv4{
                    Name:    "IPv41",
                    Address: &ipAddress1,
                    Gateway: &ipGateway1,
                    Prefix:  &ipPrefix,
                    Bgpv4: &otgclient.DeviceBgpv4{
                        Name:         "BGP Peer 1",
                        LocalAddress: &bgpLocalAddress1,
                        DutAddress:   &bgpDutAddress1,
                        RouterId:     &bgpRouterId1,
                        Active:       &bgpActive,
                        AsType:       &bgpAsType,
                        AsNumber:     &bgpAsNumber,
                        Bgpv4Routes: &[]otgclient.DeviceBgpv4Route{
                            {
                                Name:           "RR 1",
                                NextHopAddress: &nextHopAddress1,
                                Addresses: &[]otgclient.DeviceBgpv4RouteAddress{
                                    {
                                        Address: &routeAddress1,
                                        Count:   &routeCount,
                                        Step:    &routeStep,
                                        Prefix:  &routePrefix,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        {
            Name:          "DeviceGroup2",
            ContainerName: rx_port_name,
            Ethernet: otgclient.DeviceEthernet{
                Name: "Ethernet1",
                Mac:  &macAddr2,
                Mtu:  &mtu,
                Ipv4: &otgclient.DeviceIpv4{
                    Name:    "IPv41",
                    Address: &ipAddress2,
                    Gateway: &ipGateway2,
                    Prefix:  &ipPrefix,
                    Bgpv4: &otgclient.DeviceBgpv4{
                        Name:         "BGP Peer 1",
                        LocalAddress: &bgpLocalAddress2,
                        DutAddress:   &bgpDutAddress2,
                        RouterId:     &bgpRouterId2,
                        Active:       &bgpActive,
                        AsType:       &bgpAsType,
                        AsNumber:     &bgpAsNumber,
                        Bgpv4Routes: &[]otgclient.DeviceBgpv4Route{
                            {
                                Name:           "RR 1",
                                NextHopAddress: &nextHopAddress2,
                                Addresses: &[]otgclient.DeviceBgpv4RouteAddress{
                                    {
                                        Address: &routeAddress2,
                                        Count:   &routeCount,
                                        Step:    &routeStep,
                                        Prefix:  &routePrefix,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        {
            Name:          "DeviceGroup3",
            ContainerName: rx_port_name,
            Ethernet: otgclient.DeviceEthernet{
                Name: "Ethernet1",
                Mac:  &macAddr2,
                Mtu:  &mtu,
                Ipv4: &otgclient.DeviceIpv4{
                    Name:    "IPv41",
                    Address: &ipAddress2,
                    Gateway: &ipGateway2,
                    Prefix:  &ipPrefix,
                    Bgpv4: &otgclient.DeviceBgpv4{
                        Name:         "BGP Peer 1",
                        LocalAddress: &bgpLocalAddress2,
                        DutAddress:   &bgpDutAddress2,
                        RouterId:     &bgpRouterId2,
                        Active:       &bgpActive,
                        AsType:       &bgpAsType,
                        AsNumber:     &bgpAsNumber,
                        Bgpv4Routes: &[]otgclient.DeviceBgpv4Route{
                            {
                                Name:           "RR 1",
                                NextHopAddress: &nextHopAddress2,
                                Addresses: &[]otgclient.DeviceBgpv4RouteAddress{
                                    {
                                        Address: &routeAddress2,
                                        Count:   &routeCount,
                                        Step:    &routeStep,
                                        Prefix:  &routePrefix,
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    },
},
)
