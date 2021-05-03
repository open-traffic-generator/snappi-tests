#!/bin/sh
set -e

if [ "$USER" != "root" ]
  then echo "Please execute this script as sudo"
  exit
fi

if [ "${#}" != "3" ]
    then echo "usage: ${0} <name of br> <name prefix of 1st veth pair> <name prefix of 2nd veth pair>"
    exit
fi

echo "pending implementation"
exit

# new bridge
sudo brctl addbr ${1}
sudo ip link set up ${1}
# give bridge L3 interface
sudo ip addr add 172.20.0.1/24 dev ${1}
# create two veth pairs
sudo ip link add ${2}a type veth peer name ${2}b
sudo ip link add ${3}a type veth peer name ${3}b
sudo ip link set up ${2}a
sudo ip link set up ${2}b
sudo ip link set up ${3}a
sudo ip link set up ${3}b
# add veth a interfaces to bridge
sudo brctl addif ${1} ${2}a ${3}a
# give veth b interfaces an IP address
sudo ip addr add 172.20.0.2/24 dev ${2}b
sudo ip addr add 172.20.0.3/24 dev ${3}b