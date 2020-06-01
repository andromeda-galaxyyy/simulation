#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=RemoteController('c0','172.16.181.1',6633)
    net.addController(c0)


    info( '*** Add switches\n')
    s8 = net.addSwitch('s8', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s6 = net.addSwitch('s6', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s9 = net.addSwitch('s9', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s7 = net.addSwitch('s7', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch,protocols=['OpenFlow13'])
    s5 = net.addSwitch('s5', cls=OVSKernelSwitch,protocols=['OpenFlow13'])

    info( '*** Add hosts\n')
    h8 = net.addHost('h8', cls=Host, ip='10.0.0.8', defaultRoute=None, mac='00:00:00:00:00:08')
    h5 = net.addHost('h5', cls=Host, ip='10.0.0.5', defaultRoute=None, mac='00:00:00:00:00:05')
    h3 = net.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None, mac='00:00:00:00:00:03')
    h6 = net.addHost('h6', cls=Host, ip='10.0.0.6', defaultRoute=None, mac='00:00:00:00:00:06')
    h2 = net.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None, mac='00:00:00:00:00:02')
    h1 = net.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None, mac='00:00:00:00:00:01')
    h9 = net.addHost('h9', cls=Host, ip='10.0.0.9', defaultRoute=None, mac='00:00:00:00:00:09')
    h4 = net.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None, mac='00:00:00:00:00:04')
    h7 = net.addHost('h7', cls=Host, ip='10.0.0.7', defaultRoute=None, mac='00:00:00:00:00:07')

    info( '*** Add links\n')
    net.addLink(s1, s2)
    net.addLink(s2, s3)
    net.addLink(s1, s4)
    net.addLink(s4, s7)
    net.addLink(s7, s8)
    net.addLink(s8, s9)
    net.addLink(s9, s6)
    net.addLink(s6, s3)
    net.addLink(s2, s5)
    net.addLink(s4, s5)
    net.addLink(s5, s6)
    net.addLink(s5, s8)
    net.addLink(h1, s1)
    net.addLink(h2, s2)
    net.addLink(h3, s3)
    net.addLink(h4, s4)
    net.addLink(h5, s5)
    net.addLink(s6, h6)
    net.addLink(h7, s7)
    net.addLink(h8, s8)
    net.addLink(h9, s9)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s8').start([c0])
    net.get('s6').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])
    net.get('s9').start([c0])
    net.get('s1').start([c0])
    net.get('s7').start([c0])
    net.get('s4').start([c0])
    net.get('s5').start([c0])

    info( '*** Post configure switches and hosts\n')

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

