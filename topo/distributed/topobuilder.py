import os
import subprocess
from subprocess import DEVNULL
from time import sleep
from typing import List, Set, Dict, Tuple, Optional
import hashlib
from path_utils import get_prj_root
from utils.log_utils import debug, info, err, warn
from topo.distributed.traffic_scheduler import TrafficScheduler, TrafficScheduler2
import time
from utils.file_utils import check_file, create_dir, del_dir, dir_exsit, load_pkl, load_json
from topo.distributed.traffic_actor import TrafficActor
import subprocess
from utils.addr_utils import get_ipv4net_address
from utils.file_utils import del_dir, create_dir
from utils.process_utils import kill_pid
from telemetry.telemeter import Telemeter
from telemetry.base_telemeter import BaseTelemeter
from collections import defaultdict
from utils.process_utils import run_and_get_output
from topo.distributed.classifier_scheduler import ClassifierScheduler, ClassifierScheduler2

tmp_dir = os.path.join(get_prj_root(), "topo/distributed/tmp")
iptables_bk = os.path.join(tmp_dir, "iptables.bk")


def ovs_port_dump(port_str: str, filter: str, fn: str) -> int:
    command = "nohup ovs-tcpdump -U -i {} {} -l -w {}".format(
        port_str, filter, fn)
    pid = subprocess.Popen(command.split(
        " "), stdout=DEVNULL, stderr=DEVNULL).pid
    return pid


def host_port_dump(ns: str, port_str: str, filter: str, fn: str) -> int:
    command = "nohup ip netns exec {} tcpdump -U -i {} {} -l -w {}".format(
        ns, port_str, filter, fn)
    pid = subprocess.Popen(command.split(
        " "), stdout=DEVNULL, stderr=DEVNULL).pid
    return pid


def fix_path(config: Dict):
    prj_root = get_prj_root()
    config["traffic_dir"]["iot"] = os.path.join(
        prj_root, "traffic/gogen/pkts/iot")
    config["traffic_dir"]["video"] = os.path.join(
        prj_root, "traffic/gogen/pkts/video")
    config["traffic_dir"]["voip"] = os.path.join(
        prj_root, "traffic/gogen/pkts/voip")
    config["traffic_dir"]["default"] = os.path.join(
        prj_root, "traffic/gogen/pkts/default")

    config["traffic_generator"] = os.path.join(
        prj_root, "traffic/gogen/bin/gogen")
    config["listener"] = os.path.join(prj_root, "traffic/gogen/bin/golisten")


def generate_ip(id_):
    id_ = int(id_) + 1
    if 1 <= id_ <= 254:
        return "10.0.0." + str(id_)
    if 255 <= id_ <= 255 * 254 + 253:
        return "10.0." + str(id_ // 254) + "." + str(id_ % 254)
    raise Exception("Cannot support id address given a too large id")


def generate_nat_ip(id_):
    id_ = int(id_) + 1
    if 1 <= id_ <= 254:
        return "10.1.0." + str(id_)
    if 255 <= id_ <= 255 * 254 + 253:
        return "10.1." + str(id_ // 254) + "." + str(id_ % 254)
    raise Exception("Cannot support id address given a too large id")


def generate_mac(id_):
    id_ = int(id_) + 1

    def base_16(num):
        res = []
        num = int(num)
        if num == 0:
            return "0"
        while num > 0:
            left = num % 16
            res.append(left if left < 10 else chr(ord('a') + (left - 10)))
            num //= 16
        res.reverse()
        return "".join(map(str, res))

    raw_str = base_16(id_)
    if len(raw_str) > 12:
        raise Exception("Invalid id")
    # reverse
    raw_str = raw_str[::-1]
    to_complete = 12 - len(raw_str)
    while to_complete > 0:
        raw_str += "0"
        to_complete -= 1
    mac_addr = ":".join([raw_str[i:i + 2] for i in range(0, len(raw_str), 2)])
    mac_addr = mac_addr[::-1]
    return mac_addr


def gen_dpid(sid):
    sid = int(sid) + 1

    def base_16(num):
        res = []
        num = int(num)
        if num == 0:
            return "0"
        while num > 0:
            left = num % 16
            res.append(left if left < 10 else chr(ord('a') + (left - 10)))
            num //= 16
        res.reverse()
        return "".join(map(str, res))

    raw_str = base_16(sid)
    zero_padding_len = 16 - len(raw_str)
    if zero_padding_len < 0:
        raise Exception("Two large switch id")
    return ("0" * zero_padding_len) + raw_str


def add_veth(p1, p2):
    os.system("ip link add {} type veth peer name {}".format(p1, p2))


def attach_interface_to_sw(s: str, port: str):
    os.system("ovs-vsctl add-port {} {}".format(s, port))


def detach_interface_from_sw(s: str, port: str):
    os.system("ovs-vsctl del-port {} {}".format(s, port))


def del_interface(port: str):
    os.system("ip link del dev {}".format(port))


def down_interface(port: str):
    subprocess.run(["ifconfig", port, "down"])


def up_interface(port: str):
    subprocess.run(["ifconfig", port, "up"])


def del_tc(interface: str):
    os.system("tc qdisc del dev {} root".format(interface))

# todo fix this fucking bug


def add_tc(interface: str, delay=None, bandwidth=None, loss=None):
    # return
    if delay is None and bandwidth is None and loss is None:
        return
    # use hfsc
    if bandwidth is not None:
        os.system(
            "tc qdisc add dev {} root handle 5:0 hfsc default 1".format(interface))
        os.system(
            "tc class add dev {} parent 5:0 classid 5:1 hfsc sc rate {}Mbit ul rate {}Mbit".format(
                interface,
                bandwidth,
                bandwidth)
        )

    if delay is None and loss is None:
        return

    # delay and loss
    delay_loss = "tc qdisc add dev {} parent 5:1 handle 10: netem".format(
        interface)
    if delay is not None:
        delay_loss += " delay {}ms".format(delay)
    if loss is not None and int(loss) != 0:
        delay_loss += " loss {}".format(loss)
    os.system(delay_loss)


def change_tc(interface: str, delay=None, bandwidth=None, loss=None):
    # return
    if delay is None and bandwidth is None and loss is None:
        return
    # use hfsc
    if bandwidth is not None:
        os.system(
            "tc class change dev {} parent 5:0 classid 5:1 hfsc sc rate {}Mbit ul rate {}Mbit".format(
                interface,
                bandwidth,
                bandwidth)
        )

    if delay is None and loss is None:
        return

    # delay and loss
    delay_loss = "tc qdisc change dev {} parent 5:1 handle 10: netem".format(
        interface)
    if delay is not None:
        delay_loss += " delay {}ms".format(delay)
    if loss is not None and int(loss) != 0:
        delay_loss += " loss {}".format(loss)
    os.system(delay_loss)


def set_dpid(sw_id, dpid):
    sname = "s{}".format(sw_id)
    os.system(
        "ovs-vsctl set bridge {} other-config:datapath-id={}".format(sname, dpid))


def run_command_in_namespace(namespace, commands):
    os.system("ip netns exec {} {}".format(namespace, commands))


def del_ns(namespace):
    os.system("ip netns del {}".format(namespace))


def set_mtu(intf: str, mtu: int):
    mtu = int(mtu)
    os.system("ifconfig {} mtu {}".format(intf, mtu))


def set_ns_mtu(ns: str, intf: str, mtu: int):
    mtu = int(mtu)
    os.system("ip netns exec {} ifconfig {} mtu {}".format(ns, intf, mtu))


def set_mac_addr(intf: str, mac):
    os.system("ip link set {} address {}".format(intf, mac))


def set_ns_mac_addr(ns: str, intf: str, mac: str):
    os.system("ip netns exec {} ip link set {} address {}".format(ns, intf, mac))


def connect_local_switches_with_tc(sa_id, sb_id, rate, delay, loss):
    sa_name = "s{}".format(sa_id)
    sb_name = "s{}".format(sb_id)
    saport = "{}-{}".format(sa_name, sb_name)
    sbport = "{}-{}".format(sb_name, sa_name)

    os.system("ip link add {} type veth peer name {}".format(saport, sbport))
    os.system("ifconfig {} up".format(saport))
    os.system("ifconfig {} up".format(sbport))
    for x in ["gro", "tso", "gso"]:
        os.system("ethtool -K {} {} off".format(saport, x))
        os.system("ethtool -K {} {} off".format(sbport, x))
    os.system("ovs-vsctl add-port {} {}".format(sa_name, saport))
    os.system("ovs-vsctl add-port {} {}".format(sb_name, sbport))
    add_tc(saport, delay, rate, loss)
    add_tc(sbport, delay, rate, loss)

    return saport, sbport


def connect_local_switches(sa_id, sb_id):
    sa_name = "s{}".format(sa_id)
    sb_name = "s{}".format(sb_id)
    saport = "{}-{}".format(sa_name, sb_name)
    sbport = "{}-{}".format(sb_name, sa_name)

    os.system("ip link add {} type veth peer name {}".format(saport, sbport))
    os.system("ifconfig {} up".format(saport))
    os.system("ifconfig {} up".format(sbport))
    for x in ["gro", "tso", "gso"]:
        os.system("ethtool -K {} {} off".format(saport, x))
        os.system("ethtool -K {} {} off".format(sbport, x))
    os.system("ovs-vsctl add-port {} {}".format(sa_name, saport))
    os.system("ovs-vsctl add-port {} {}".format(sb_name, sbport))

    return saport, sbport


def connect_non_local_switches_with_tc(sa_id, local_ip, sb_id, remote_ip, grekey, rate, delay, loss,
                                       gre_mtu=1554):
    local_sw = "s{}".format(sa_id)
    remote_sw = "s{}".format(sb_id)
    grename = "{}-{}".format(local_sw, remote_sw)
    # delete exists gre links
    # os.system("ip link del {}".format(grename))
    del_interface(grename)
    gre_command = "ip link add {} type gretap local {} remote {} ttl 64 key {}".format(
        grename,
        local_ip,
        remote_ip,
        grekey
    )
    os.system(gre_command)
    attach_interface_to_sw(local_sw, grename)

    gre_mtu = int(gre_mtu)
    set_mtu(grename, gre_mtu)
    for x in ["gro", "tso", "gso"]:
        os.system("ethtool -K {} {} off".format(grename, x))
    os.system("ip link set dev {} up".format(grename))
    add_tc(grename, delay, rate, loss)
    return grename


def connect_non_local_switches(sa_id, local_ip, sb_id, remote_ip, grekey,
                               gre_mtu=1554):
    local_sw = "s{}".format(sa_id)
    remote_sw = "s{}".format(sb_id)
    grename = "{}-{}".format(local_sw, remote_sw)
    # delete exists gre links
    # os.system("ip link del {}".format(grename))
    del_interface(grename)
    gre_command = "ip link add {} type gretap local {} remote {} ttl 64 key {}".format(
        grename,
        local_ip,
        remote_ip,
        grekey
    )
    os.system(gre_command)
    attach_interface_to_sw(local_sw, grename)

    gre_mtu = int(gre_mtu)
    set_mtu(grename, gre_mtu)
    for x in ["gro", "tso", "gso"]:
        os.system("ethtool -K {} {} off".format(grename, x))
    os.system("ip link set dev {} up".format(grename))
    return grename


def add_hosts_to_switches(switch_id, k, vhost_mtu=1500, tcpdump=False, filter_str: str = "udp",
                          base_dir="/tmp/tcpdump"):
    ovsname = "s{}".format(switch_id)
    mtu = int(vhost_mtu)
    for idx in range(k):
        host_id = switch_id * k + idx
        hostname = "h{}".format(host_id)
        host_port = "{}-eth0".format(hostname)
        ovs_port = "{}-{}".format(ovsname, hostname)

        os.system("ip netns add {}".format(hostname))
        os.system("ip link add {} type veth peer name {}".format(
            host_port, ovs_port))
        os.system("ip link set {} netns {}".format(host_port, hostname))

        # up host interface
        # 10.0.0.1/16
        # 修改子网为10.0.0.1/16
        os.system(
            "ip netns exec {} ifconfig {} {}/16".format(hostname, host_port, generate_ip(host_id)))
        for x in ["gro", "tso", "gso"]:
            os.system(
                "ip netns exec {} ethtool -K {} {} off".format(
                    hostname, host_port, x)
            )

        os.system("ip netns exec {} ifconfig lo up".format(hostname))
        set_ns_mac_addr(hostname, host_port, generate_mac(host_id))
        set_ns_mtu(hostname, host_port, mtu)

        # attach ovs port
        attach_interface_to_sw(ovsname, ovs_port)
        for x in ["gro", "tso", "gso"]:
            os.system("ethtool -K {} {} off".format(ovs_port, x))

        up_interface(ovs_port)
        if tcpdump:
            # ovs port
            fn = os.path.join(base_dir, "{}.pcap".format(ovs_port))
            ovs_port_dump(ovs_port, filter_str, fn)
            sleep(0.1)
            # host port
            fn = os.path.join(base_dir, "{}.pcap".format(host_port))
            host_port_dump(hostname, host_port, filter_str, fn)
            sleep(0.1)


def add_ovs(switch_id, controller: str):
    ovs_name = "s{}".format(switch_id)
    # debug("set up switch {} controller:{}".format(ovs_name,controller))
    dpid = gen_dpid(switch_id)
    os.system(
        "ovs-vsctl add-br {} -- set bridge {} protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13 other-config:datapath-id={}".format(
            ovs_name, ovs_name, dpid))
    os.system("ovs-vsctl set-controller {} tcp:{}".format(ovs_name, controller))
    debug("set up switch {} done".format(ovs_name))


def del_ovs(ovs):
    if "s" not in ovs:
        ovs = "s{}".format(ovs)
    os.system("ovs-vsctl del-br {}".format(ovs))


def del_hosts(ovs, k):
    if "s" not in ovs:
        ovs = "s{}".format(ovs)

    for idx in range(k):
        host_id = ovs * k + idx
        host_port = "{}-eth0".format(host_id)
        hostname = "h{}".format(host_id)
        ovs_port = "{}-{}".format(hostname, ovs)
        os.system("ip netns del {}".format(hostname))
        os.system("ip link del {}".format(host_port))


def del_local_link(link_name):
    del_interface(link_name)
    del_tc(link_name)


def get_swid_from_link(link: str):
    '''
    split switch from link name
    :param link: like gres1-s2 or s1-s2
    :return:
    '''
    if "gre" in link:
        link = link[3:]
    sa_name, sb_name = link.split("-")
    # return link.split("s")[1], link.split("s")[2]
    return int(sa_name[1:]), int(sb_name[1:])


def run_ns_binary(ns: str, bin: str, params: str, log_fn: str = "/tmp/log.log"):
    os.system("ip netns exec {} nohup {} {} >{} 2>&1 &".format(
        ns, bin, params, log_fn))


def add_bandwidth_contraits_with_ovsset(port: str, band: int):
    os.system(
        "ovs-vsctl set interface {}  ingress_policing_rate={}".format(port, band*1100))
    os.system(
        "ovs-vsctl set interface {}  ingress_policing_burst={}".format(port, band*1100))


class TopoBuilder:
    def __init__(self, config: dict, id_, inetintf: str):
        self.config: dict = config
        fix_path(config)
        debug(config)

        self.id = id_
        # self.gres: List[str] = []
        self.gres = set()
        self.gre_keys = {}
        self.inetintf = inetintf

        self.local_switch_ids: List[int] = config["workers"][self.id]

        # dict switch->worker id
        self.remote_switches = {}
        # parse remote switches
        for idx, switches in enumerate(config["workers"]):
            if self.id == int(idx):
                continue
            #
            for s in switches:
                self.remote_switches[s] = idx

        debug(self.local_switch_ids)
        debug(self.remote_switches)

        self.local_links = set()
        self.nat_links: List[str] = []

        self.hosts: List[tuple] = []
        self.remote_ips: List[str] = config["workers_ip"]
        # self.ip: str = config["workers_ip"][self.id]

        self.tcpdump = False
        self.tcpdump_opts = {
            "base_dir": "",
            "filter": "",
        }
        self.tcpdump_pids = {}
        self.tcpdump_ports = []
        if "debug" in self.config.keys():
            if "tcpdump" in self.config["debug"].keys():
                if int(self.config["debug"]["tcpdump"]["enable"]) == 1:
                    debug("Enable ovs port tcpdump")
                    self.tcpdump = True
                    self.tcpdump_opts["filter"] = self.config["debug"]["tcpdump"]["filter"]
                    self.tcpdump_opts["base_dir"] = self.config["debug"]["tcpdump"]["base_dir"]
                    del_dir(self.tcpdump_opts["base_dir"])
                    create_dir(self.tcpdump_opts["base_dir"])

        self.hostids = []
        self._set_up_switches()
        mtu = self.config["host_mtu"]
        set_mtu(self.inetintf, mtu)
        self._populate_gre_key()
        self._write_targetids()

        self.traffic_scheduler = TrafficScheduler2(self.config, self.hostids)
        self.host_found = False
        self.traffic_actor = TrafficActor(self.config, self.hostids)
        self.telemeter: BaseTelemeter = None
        self.vars = {
            "tc": {}
        }

        self.classifier_scheduler: ClassifierScheduler2 = ClassifierScheduler2(
            self.config, self.hostids)

    def _set_up_switches(self):
        k = self.config["host_per_switch"]
        k = int(k)
        controller = self.config["controller"]
        # set up local switch
        vhost_mtu = self.config["vhost_mtu"]
        for sw_id in self.config["workers"][int(self.id)]:
            add_ovs(sw_id, controller)
            add_hosts_to_switches(sw_id, k, vhost_mtu, self.tcpdump, self.tcpdump_opts["filter"],
                                  self.tcpdump_opts["base_dir"])
            for hostidx in range(k):
                hostid = sw_id * k + hostidx
                self.hostids.append(hostid)
        self._set_up_nat()

        if int(self.config["enable_listener"]) == 1:
            debug("Set up traffic listener")
            self._set_up_listener()
            debug("Set up traffic listener done")

    def _populate_gre_key(self):
        gre_ = 1
        n_switches = self.config["n_switches"]
        n_switches = int(n_switches)
        for src in range(n_switches):
            for dst in range(n_switches):
                if src >= dst:
                    continue
                key = "s{}s{}".format(src, dst)
                self.gre_keys[key] = gre_
                gre_ += 1

    def _get_gre_key(self, sa_id, sb_id):
        '''
        get gre key from sa_id to sb_id
        :param sa_id: src_id
        :param sb_id: dst_id
        :return:
        '''
        sa_id = int(sa_id)
        sb_id = int(sb_id)
        if sa_id > sb_id:
            return self._get_gre_key(sb_id, sa_id)
        key = "s{}s{}".format(sa_id, sb_id)
        return self.gre_keys[key]

    def _tear_down_switch(self):
        k = self.config["host_per_switch"]
        k = int(k)
        for sid in self.local_switch_ids:
            sw_name = "s{}".format(sid)
            debug("Tearing down {}".format(sw_name))
            for idx in range(k):
                hostid = sid * k + idx
                hostname = "h{}".format(hostid)
                host_port = "{}-eth0".format(hostname)
                del_ns(hostname)
                del_interface(host_port)

                ovs_port = "{}-{}".format(sw_name, hostname)
                detach_interface_from_sw(sw_name, ovs_port)
                del_interface(ovs_port)
            del_ovs(sw_name)
            debug("tear down {} done".format(sw_name))

    def _tear_down_gres(self):
        for gre in self.gres:
            s, _ = get_swid_from_link(gre)
            s = "s{}".format(s)
            detach_interface_from_sw(s, gre)
            del_tc(gre)
            down_interface(gre)
            del_interface(gre)

    def _tear_down_local_links(self):
        # debug(self.local_links)
        for link in self.local_links:
            del_local_link(link)

    def tear_down(self):
        self._tear_down_gres()
        self._tear_down_local_links()
        self._tear_down_switch()
        self._tear_down_nat()

        self.gres = []
        self.local_switch_ids = []
        self.remote_switches = {}
        self.local_links = []
        self.hosts = []
        self.nat_links = []
        self.vars = {
            "tc": {}
        }
        cmd = "for bridge in `ovs-vsctl list-br`;" \
            "do " \
            "ovs-vsctl del-br $bridge " \
            "echo '$bridge' deleted " \
            "done"
        os.system(cmd)

    def _diff_local_links(self, new_topo: List[List[Tuple]]):
        debug("diff local links")
        new_links = set()

        local_switch_ids = [int(x) for x in self.local_switch_ids]
        for sa_id in local_switch_ids:
            for sb_id in local_switch_ids:
                # remove duplicates
                if sa_id == sb_id or sa_id > sb_id:
                    continue

                link = "s{}-s{}".format(sa_id, sb_id)
                reverse_link = "s{}-s{}".format(sb_id, sa_id)

                if -1 not in new_topo[sa_id][sb_id]:
                    rate, delay, loss, _ = new_topo[sa_id][sb_id]
                    rate = rate if int(
                        self.config["enable_rate_constraint"]) == 1 else None
                    delay = delay if (int(
                        self.config["enable_delay_constraint"]) == 1 and delay > 0) else None
                    loss = loss if (
                        int(self.config["enable_loss_constraint"]) == 1 and loss > 0) else None
                    new_links.add(link)
                    new_links.add(reverse_link)
                    if link not in self.local_links:
                        # 如果主机还没有发现（启动ping），说明是第一次建立拓扑，那么就不应该设置链路qos,等第一次建立topo以后
                        # 然后设置ping
                        if not self.host_found:
                            connect_local_switches(sa_id, sb_id)
                            self.vars["tc"][reverse_link] = (rate, delay, loss)
                            self.vars["tc"][link] = (rate, delay, loss)
                        else:
                            connect_local_switches_with_tc(
                                sa_id, sb_id, rate, delay, loss)
                        # todo 在拓扑变换的时候，可能覆盖掉之前抓取的包
                        if self.tcpdump:
                            # sleep(0.5)
                            fn = os.path.join(
                                self.tcpdump_opts["base_dir"], "{}.pcap".format(link))
                            self.tcpdump_pids[link] = ovs_port_dump(link,
                                                                    self.tcpdump_opts["filter"], fn)
                            # sleep(0.2)
                            fn = os.path.join(self.tcpdump_opts["base_dir"],
                                              "{}.pcap".format(reverse_link))
                            self.tcpdump_pids[reverse_link] = ovs_port_dump(reverse_link,
                                                                            self.tcpdump_opts[
                                                                                "filter"], fn)

                    else:
                        # exists in previous local links,
                        # change tc
                        # del_tc(link)
                        # del_tc(reverse_link)
                        change_tc(link, delay, rate, loss)
                        change_tc(reverse_link, delay, rate, loss)
                else:
                    # link is None
                    if link in self.local_links:
                        if link in self.tcpdump_pids.keys():
                            kill_pid(self.tcpdump_pids[link])
                        if reverse_link in self.tcpdump_pids.keys():
                            kill_pid(self.tcpdump_pids[reverse_link])

                        del_tc(link)
                        del_tc(reverse_link)
                        detach_interface_from_sw("s{}".format(sa_id), link)
                        detach_interface_from_sw(
                            "s{}".format(sb_id), reverse_link)
                        del_interface(link)
                        del_interface(reverse_link)
        self.local_links = new_links

    def _diff_gre_links(self, new_topo: List[List[Tuple]]):
        gre_mtu = self.config["gre_mtu"]
        debug("Setting up gre links")
        new_gres = set()
        local_sw_ids = [int(x) for x in self.local_switch_ids]
        remote_sw_ids = [int(x) for x in self.remote_switches.keys()]

        # # calculate all gre setup
        n_workers = len(self.config["workers"])
        debug("#workers {}".format(n_workers))

        # collect all  switch id to worker_id
        swid_to_worker_id = {}
        for worker_id in range(n_workers):
            for sid in self.config["workers"][worker_id]:
                swid_to_worker_id[sid] = worker_id

        worker_id_to_gre = defaultdict(lambda: [])
        for said in range(len(new_topo)):
            for sbid in range(len(new_topo[0])):
                if said >= sbid:
                    continue
                if -1 in new_topo[said][sbid]:
                    continue
                if swid_to_worker_id[said] == swid_to_worker_id[sbid]:
                    continue
                # now we find grep
                # said<sbid
                gre = "s{}-s{}".format(said, sbid)
                # reverse_gre="s{}-s{}".format(sbid,said)
                worker_id_to_gre[swid_to_worker_id[said]].append(gre)
                worker_id_to_gre[swid_to_worker_id[sbid]].append(gre)

        # map gre to worker id
        # map gre to local ip
        '''
		对于每个worker来说，只要确定了localip就行，比如w0和w1是两个worker, 只需要为两个worker分别分配localip，那么	
		w0 包含 s1,
		w2 包含 s2 
		gre_local_ip[0]={"s1-s2":"192.168.1.2","s2-s1":"192.168.1.2"}
		gre_local_ip[1]={"s1-s2":"192.168.1.3","s2-s1":"192.168.1.3"}
		确定localip
		对于一个worker来说，只要按顺序选择localip,然后选择对应的localip就行了
		'''
        gre_to_local_ip = [defaultdict(lambda:None) for _ in range(n_workers)]
        for worker_id in range(n_workers):
            worker_id_to_gre[worker_id].sort()
            content = gre_to_local_ip[worker_id]
            local_ips = self.config["workers_ip"][worker_id]
            for idx, gre in enumerate(worker_id_to_gre[worker_id]):
                n_local_ips = len(local_ips)
                ip = local_ips[idx % n_local_ips]
                content[gre] = ip
                reverse_gre = gre.split("-")[1]+"-"+gre.split("-")[0]
                content[reverse_gre] = ip

        for sa_id in local_sw_ids:
            sa_worker_id = swid_to_worker_id[sa_id]
            for sb_id in remote_sw_ids:
                sb_worker_id = swid_to_worker_id[sb_id]
                key = self._get_gre_key(sa_id, sb_id)
                gretap = "s{}-s{}".format(sa_id, sb_id)

                # local_ip = self.ip
                # # mapping from worker id to remote ip
                # remote_ip = self.remote_ips[int(self.remote_switches[sb_id])]

                if -1 in new_topo[sa_id][sb_id]:
                    if gretap in self.gres:
                        if gretap in self.tcpdump_pids.keys():
                            kill_pid(self.tcpdump_pids[gretap])
                        # take down gre
                        down_interface(gretap)
                        detach_interface_from_sw("s{}".format(sa_id), gretap)
                        del_tc(gretap)
                        del_interface(gretap)

                else:
                    local_ip = gre_to_local_ip[sa_worker_id][gretap]
                    remote_ip = gre_to_local_ip[sb_worker_id][gretap]
                    debug("gre link {} local ip {} remote ip {}".format(
                        gretap, local_ip, remote_ip))
                    # debug("setting up gre {}".format(gretap))
                    rate, delay, loss, _ = new_topo[sa_id][sb_id]
                    rate = rate if int(
                        self.config["enable_rate_constraint"]) == 1 else None
                    delay = delay if (int(
                        self.config["enable_delay_constraint"]) == 1 and delay > 0) else None
                    loss = loss if (
                        int(self.config["enable_loss_constraint"]) == 1 and loss > 0) else None
                    # debug("bandwidth:{};delay:{}".format(rate,delay))
                    new_gres.add(gretap)
                    if gretap in self.gres:
                        # del tc
                        change_tc(gretap, delay, rate, loss)
                    else:
                        # set up gre
                        if not self.host_found:
                            self.vars["tc"][gretap] = (rate, delay, loss)
                            connect_non_local_switches(
                                sa_id, local_ip, sb_id, remote_ip, key, gre_mtu)
                        else:
                            connect_non_local_switches_with_tc(sa_id, local_ip, sb_id, remote_ip, key, rate,
                                                               delay, loss, gre_mtu)
                        if self.tcpdump:
                            # sleep(0.5)
                            fn = os.path.join(self.tcpdump_opts["base_dir"],
                                              "{}.pcap".format(gretap))
                            self.tcpdump_pids[gretap] = ovs_port_dump(
                                gretap, self.tcpdump_opts["filter"], fn)

                        # sleep(0.2)

        self.gres = new_gres

    def diff_topo(self, new_topo: List[List[Tuple]]):
        debug("start diff topo")
        self._diff_local_links(new_topo)
        self._diff_gre_links(new_topo)
        if not self.host_found:
            info("Wait for all links setup")
            time.sleep(20)
            self._do_find_host()
            self.host_found = True
            # setup up tc
            for _, (link, qos) in enumerate(self.vars["tc"].items()):
                rate, delay, loss = qos
                # rate = delay if int(self.config["enable_rate_constraint"]) == 1 else None
                # delay = delay if int(
                # 	self.config["enable_delay_constraint"]) == 1 else None
                # loss = loss if int(self.config["enable_loss_constraint"]) == 1 else None

                add_tc(link, delay, rate, loss)
                debug("Add tc for {} done".format(link))

        debug("diff topo done")
        self.telemeter = Telemeter(
            self.local_switch_ids, new_topo, self.config)

    def _set_up_nat(self):
        debug("Setting up nat")
        os.system("echo '1' > /proc/sys/net/ipv4/ip_forward")
        intf = self.inetintf
        # get ip addr of intf
        # cmd="ip -o -f inet addr show |grep "+intf+" | awk '/scope global/ {print $4}'"
        # ip=None
        # try:
        # 	ip=run_and_get_output(cmd)
        # except Exception as e:
        # 	err("cannot get ip address of {}".format(intf))
        # 	err(str(e))
        #
        # warn("if your intf ip address does'nt stay in the same network as redis,some function may not work")
        #
        # subnet=get_ipv4net_address(ip)
        # #change ip route metric
        # info("change ip route metric")
        # os.system("ip route add {} dev {} metric 1".format(subnet,intf))
        # info("change ip route metric done")
        worker_id = self.id
        nat2_ip = "10.1.0.254"
        debug("nat out ip {}/16".format(nat2_ip))
        os.system("ovs-vsctl add-br nat")
        # os.system("ip link add nat1 type veth peer name nat2")
        add_veth("nat1", "nat2")
        os.system("ifconfig nat2 {}/16 up".format(nat2_ip))
        attach_interface_to_sw("nat", "nat1")
        # os.system("ovs-vsctl add-port nat nat1")
        os.system("ifconfig nat1 up")

        # set iptables
        os.system("iptables -A FORWARD -o {} -i {} -j ACCEPT".format("nat2", intf))
        os.system("iptables -A FORWARD -o {} -i {} -j ACCEPT".format(intf, "nat2"))
        os.system(
            "iptables -t nat -A POSTROUTING -s 10.1.0.0/16 -o {} -j MASQUERADE".format(intf))

        # set add link to host
        # 改成从命令行接受
        k = int(self.config["host_per_switch"])
        local_switches = self.config["workers"][worker_id]

        for swid in local_switches:
            for hostidx in range(k):
                hostid = swid * k + hostidx
                hostname = "h{}".format(hostid)
                hnat = "{}-{}".format(hostname, "nat")
                nath = "{}-{}".format("nat", hostname)
                add_veth(hnat, nath)
                self.nat_links.append(hnat)
                self.nat_links.append(nath)
                # set netns
                os.system("ip link set {} netns {}".format(hnat, hostname))
                nat_ip = generate_nat_ip(hostid)
                os.system(
                    "ip netns exec {} ifconfig {} {}/16 up".format(hostname, hnat, nat_ip))
                # attach port
                os.system("ovs-vsctl add-port {} {}".format("nat", nath))
                os.system("ifconfig {} up".format(nath))

                # set default route
                os.system(
                    "ip netns exec {} ip route add default via {}".format(hostname, nat2_ip))
        debug("Setting up nat done")

    def _tear_down_nat(self):
        debug("Tearing down nat")
        os.system("ovs-vsctl del-br nat")
        del_interface("nat1")
        del_interface("nat2")

        # tear down
        for p in self.nat_links:
            del_interface(p)

        commands = "iptables -F"
        os.system(commands)
        debug("Tearing down nat done")

    def start_gen_traffic(self):
        self._write_targetids()
        binary = self.config["traffic_generator"]

        pkt_dir = self.config["traffic_dir"]["default"]
        vhost_mtu = int(self.config["vhost_mtu"])
        controller_ip = self.config["controller"].split(":")[0]
        controller_socket_port = int(self.config["controller_socket_port"])
        target_id_dir = os.path.join(
            get_prj_root(), "topo/distributed/targetids")

        worker_id = self.id
        k = int(self.config["host_per_switch"])
        local_switches = self.config["workers"][worker_id]
        for swid in local_switches:
            for host_idx in range(k):
                hostid = swid * k + host_idx
                hostname = "h{}".format(hostid)
                target_id_fn = os.path.join(
                    target_id_dir, "{}.targetids".format(hostname))
                hostname = "h{}".format(hostid)
                host_intf = "h{}-eth0".format(hostid)
                log_fn = "/tmp/{}.gen.log".format(hostid)

                params = "--id {} " \
                         "--dst_id {} " \
                         "--pkts {} " \
                         "--mtu {} " \
                         "--int {} " \
                         "--cip {} " \
                         "--cport {}".format(
                             hostid,
                             target_id_fn,
                             pkt_dir,
                             vhost_mtu,
                             host_intf,
                             controller_ip,
                             controller_socket_port,
                         )
                run_ns_binary(hostname, binary, params, log_fn)

    def stop_traffic(self):
        os.system("for p in `pgrep '^gen$'`;do kill $p;done")
        os.system("pkill -f '^golisten$'")
        self._stop_traffic_scheduler()

    def __stop_tcpdump(self):
        for l in self.tcpdump_pids.keys():
            kill_pid(self.tcpdump_pids[l])
        os.system("pkill tcpdump")
        os.system("pkill ovs-tcpdump")

    def stop(self):
        self.stop_traffic()
        self.stop_traffic_use_scheduler()
        time.sleep(5)
        self._stop_listener()
        time.sleep(5)
        self._stop_traffic_scheduler()
        self.stop_traffic_actor()
        self.tear_down()
        os.system("iptables-restore < {}".format(iptables_bk))
        self.__stop_tcpdump()
        self.stop_telemetry()
        self.stop_classifier_demo()

    def _write_targetids(self):
        target_id_dir = os.path.join(
            get_prj_root(), "topo/distributed/targetids")
        all_switches = []
        k = int(self.config["host_per_switch"])
        worker_id = self.id
        local_switches = self.config["workers"][worker_id]
        for switches in self.config["workers"]:
            all_switches.extend(switches)

        for swid in local_switches:
            target_switches = [x for x in all_switches if x != swid]
            target_host_ids = []
            for target_swid in target_switches:
                for host_idx in range(k):
                    target_host_id = target_swid * k + host_idx
                    target_host_ids.append(target_host_id)

            for host_idx in range(k):
                host_id = swid * k + host_idx
                hostname = "h{}".format(host_id)
                with open(os.path.join(target_id_dir, "{}.targetids".format(hostname)), 'w') as fp:
                    for target_id in target_host_ids:
                        fp.write("{}\n".format(target_id))
                    fp.flush()
                    fp.close()
        debug("Write targetid done")

    def _start_traffic_scheduler(self):
        scheduler = self.traffic_scheduler
        scheduler.start()

    def _stop_traffic_scheduler(self):
        self.traffic_scheduler.stop()

    def start_gen_traffic_use_scheduler(self):
        self._start_traffic_scheduler()

    def stop_traffic_use_scheduler(self):
        self._stop_traffic_scheduler()

    def _do_find_host(self):
        hostname = "h{}".format(self.hostids[0])
        for targetid in self.hostids:
            os.system(
                "ip netns exec {} ping {} -c 1".format(hostname, generate_ip(targetid)))

    def _set_up_listener(self):
        listener_binary = self.config["listener"]
        base_dir = self.config["listener_log_base_dir"]

        if dir_exsit(base_dir):
            del_dir(base_dir)
        create_dir(base_dir)

        check_file(listener_binary)

        for hid in self.hostids:
            hostname = "h{}".format(hid)
            hintf = "{}-eth0".format(hostname)
            delay_dir = os.path.join(base_dir, "{}.rx.delay".format(hid))
            # if dir_exsit(delay_dir):
            # 	del_dir(delay_dir)
            # create_dir(delay_dir)
            #
            loss_dir = os.path.join(base_dir, "{}.rx.loss".format(hid))
            log_fn = os.path.join("/tmp/{}.listener.log".format(hostname))
            enable_loss = (int(self.config["enable_loss"]) == 1)

            os.system("ip netns exec {} nohup {} --intf {} {} {} --delay_dir {}>{} 2>&1 &".format(
                hostname,
                listener_binary,
                hintf,
                ("--loss " if enable_loss else ""),
                ("--loss_dir {}".format(loss_dir) if enable_loss else ""),
                delay_dir,
                log_fn))

    def _stop_listener(self):
        os.system("for p in `pgrep '^golisten$'`;do kill $p;done")

    def diff_traffic_mode(self, mode):
        self.traffic_actor.act(mode)

    def stop_traffic_actor(self):
        self.traffic_actor.stop()

    def setup_supplementary_topo2(self, band):
        if self.id != 0:
            debug("nothing to do,return")
            return

        debug("set band to {}Mbps".format(band))
        add_bandwidth_contraits_with_ovsset("s{}-s{}".format(9, 10), band)
        add_bandwidth_contraits_with_ovsset("s{}-s{}".format(10, 9), band)
        add_bandwidth_contraits_with_ovsset("s{}-s{}".format(11, 10), 20)
        add_bandwidth_contraits_with_ovsset("s{}-s{}".format(10, 11), 20)

        # ens1f0
        attach_interface_to_sw("s{}".format(10), "ens1f0")
        up_interface("ens1f0")
        attach_interface_to_sw("s{}".format(8), "ens1f1")
        up_interface("ens1f1")
        # ens1f1:

    def setup_anomaly_supplementary_topo(self):
        if self.id != 0:
            debug("nothing todo return")
            return

        attach_interface_to_sw("s{}".format(2), "ens5f0")
        up_interface("ens5f0")
        attach_interface_to_sw("s{}".format(5), "ens5f1")
        up_interface("ens5f1")

    def setup_supplementary_topo(self, is_server: bool = True):

        supp_topos = self.config["supplementary"]
        ovs_id = 11
        if ovs_id not in self.local_switch_ids:
            return

        controller = self.config["controller"]
        ovs_name = "s{}".format(ovs_id)

        access_id = 69
        access_name = "s{}".format(access_id)
        add_ovs(access_id, controller)
        p3, p4 = "{}-{}".format(access_name,
                                ovs_name), "{}-{}".format(ovs_name, access_name)
        add_veth(p3, p4)
        attach_interface_to_sw(access_name, p3)
        up_interface(p3)
        attach_interface_to_sw(ovs_name, p4)
        up_interface(p4)

        server_accessid = 67
        client_accessid = 68
        server_access = "s{}".format(server_accessid)
        add_ovs(server_accessid, controller)
        client_access = "s{}".format(client_accessid)
        add_ovs(client_accessid, controller)

        p1, p2 = "{}-{}".format(access_name,
                                server_access), "{}-{}".format(server_access, access_name)
        add_veth(p1, p2)
        attach_interface_to_sw(access_name, p1)
        attach_interface_to_sw(server_access, p2)
        up_interface(p1)
        up_interface(p2)
        os.system(
            "ovs-vsctl set interface {}  ingress_policing_rate=5000".format(p1))
        os.system(
            "ovs-vsctl set interface {}  ingress_policing_rate=5000".format(p2))
        # os.system("ovs-vsctl set interface {}  ingress_policing_burst=10000".format(p1))
        # os.system("ovs-vsctl set interface {}  ingress_policing_burst=10000".format(p2))
        # add_tc(p1,bandwidth=5,delay=None,loss=None)
        # add_tc(p2,bandwidth=5,delay=None,loss=None)

        attach_interface_to_sw(server_access, "enp59s0f0")
        up_interface("enp59s0f0")

        p3, p4 = "{}-{}".format(access_name,
                                client_access), "{}-{}".format(client_access, access_name)
        add_veth(p3, p4)
        attach_interface_to_sw(access_name, p3)
        attach_interface_to_sw(client_access, p4)
        up_interface(p3)
        up_interface(p4)
        attach_interface_to_sw(client_access, "enp59s0f1")
        up_interface("enp59s0f1")

        return
        # add_tc(p1,bandwidth=5,delay=None,loss=None)
        # add_tc(p2,bandwidth=5,delay=None,loss=None)

        # access_id=67
        # controller = self.config["controller"]
        # add_ovs(access_id, controller)
        # access_name="s{}".format(access_id)
        #
        # p1, p2 = "{}-{}".format(ovs_name, access_name), "{}-{}".format(access_name, ovs_name)
        # add_veth(p1, p2)
        # attach_interface_to_sw(ovs_name,p1)
        # attach_interface_to_sw(access_name,p2)
        # up_interface(p1)
        # up_interface(p2)
        #
        #
        # intfs=supp_topos[0]["intfs"]
        # qos=supp_topos[0]["qos"][0]
        # attach_interface_to_sw(access_name,intfs[0])
        # up_interface(intfs[0])
        #
        # attach_interface_to_sw(access_name,intfs[1])
        # add_tc(intfs[0],bandwidth=band)
        #
        #
        # up_interface(intfs[1])
        # band=qos[0]
        # add_tc(intfs[0],bandwidth=band)
        # add_tc(intfs[0],bandwidth=band)
        # return

        # supp_topos = self.config["supplementary"]
        # supp_topo = None
        # ovs_id = -1
        # for t in supp_topos:
        # 	if is_server and t["tag"] == "server":
        # 		supp_topo = t
        # 		# todo how to eliminate this constant
        # 		ovs_id = 66
        # 		break
        # 	elif (not is_server) and t["tag"] == "client":
        # 		supp_topo = t
        # 		ovs_id = 67
        # 		break
        #
        # if ovs_id == -1:
        # 	debug("Nothing to do;return from setup_supplementary_topo")
        # 	return

        # controller = self.config["controller"]
        # add_ovs(ovs_id, controller)
        # attach_interface_to_sw(ovs_name, supp_topo["intf"])
        # up_interface(supp_topo["intf"])
        #
        # neighbors = supp_topo["neighbors"]
        # debug("set up supplementary topo for {}".format(supp_topo["tag"]))
        # for nidx, neighbor in enumerate(neighbors):
        # 	qos = supp_topo["qos"][nidx]
        # 	band = qos[0]
        # 	delay = qos[1]
        # 	n = "s{}".format(neighbor)
        # 	p1, p2 = "{}-{}".format(ovs_name, n), "{}-{}".format(n, ovs_name)
        # 	add_veth(p1, p2)
        #
        # 	attach_interface_to_sw(ovs_name, p1)
        # 	attach_interface_to_sw(n, p2)
        # 	up_interface(p1)
        # 	up_interface(p2)
        #
        # 	if is_server:
        # 		add_tc(p1, bandwidth=band, delay=None)
        # 		add_tc(p2, bandwidth=band, delay=None)

    def start_telemetry(self):
        if self.telemeter is not None:
            self.telemeter.start(None)

    def stop_telemetry(self):
        if self.telemeter is not None:
            self.telemeter.stop()

    def start_classifier_demo(self):
        if self.classifier_scheduler is not None:
            self.classifier_scheduler.start()
            debug("classifier scheduler start")
            return
        err("classifier scheduler not initiated")

    def stop_classifier_demo(self):
        if self.classifier_scheduler is not None:
            self.classifier_scheduler.stop()
            debug("classifier scheduler stop")
            return
        err("classfifier scheduler not initiated")

    def start_anomaly_traffic(self):
        self.traffic_actor.start_anomaly_traffic()

    def stop_anomaly_traffic(self):
        self.traffic_actor.stop_anomaly_traffic()


if __name__ == '__main__':
    config = load_json(os.path.join(
        get_prj_root(), "topo/distributed/satellite.config.json"))
    builder = TopoBuilder(config, 0, "ens33")
