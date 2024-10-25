#!/usr/bin/env python

import subprocess
import re
import json

def run_tshark():
    # Define the tshark command with timeout
    tshark_cmd = [
        'sudo', 'timeout', '60', 'tshark', '-i', 'ens192', '-f', 'tcp port 6653',
        '-Y', 'openflow_v4', '-O', 'openflow_v4'
    ]

    # Open a file to write the output
    with open('tshark_output.txt', 'w') as file:
        # Run the tshark command
        process = subprocess.Popen(tshark_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Write the output to the file
        file.write(stdout.decode())

def parse_openflow_messages(file_path):
    # Read the file content
    with open(file_path, 'r') as file:
        output = file.read()
    # Regular expression to find Features Reply messages and extract datapath_id
    features_reply_pattern = re.compile(r'OFPT_FEATURES_REPLY.*?datapath_id: (0x[0-9a-fA-F]+)', re.DOTALL)
    matches = features_reply_pattern.findall(output)
    #catprint("Datapath ID Matches:", matches)
    #datapath_ids = set(matches)
    return matches

def extract_ip_address(file_path):
    # Read the file content
    with open(file_path, 'r') as file:
        output = file.read()
    # Regular expression to find Features Reply messages and extract source IP
    ip_pattern = re.compile(r'OFPT_FEATURES_REPLY.*?Src: (\d+\.\d+\.\d+\.99+)', re.DOTALL)
    matches = ip_pattern.findall(output)
    #print("IP Matches:", matches)
    #ips = set(matches)
    return matches

def connected():
    run_tshark()
    datapath_ids = parse_openflow_messages('tshark_output.txt')
    if datapath_ids:
        print("Switches successfully connected to the controller:")
        for dpid in datapath_ids:
            print("Switch connected with datapath_id: {}".format(dpid))
    else:
        print("No successful connections detected.")

def ipconnecttest():
    getip = extract_ip_address('tshark_output.txt')
    if getip:
        print("Switches successfully connected to the controller:")
        for ip in getip:
            print("Switches connected from ip: {}".format(ip))
    else:
        print("No successful connections detected.")

def jfile():
    dpids = parse_openflow_messages('tshark_output.txt')
    ips = extract_ip_address('tshark_output.txt')

    # Create a dictionary to store dpid and ip information
    switch_data = {}

    # If there are more dpids than ips, we'll assign the available IPs to each dpid
    for dpid in dpids:
        ip = ips[0]  # Use the first available IP, assuming all switches share it
        switch_data[dpid] = {
            "ip_address": ip,
            "status": "connected"
        }

    # Write the dictionary to a JSON file
    with open('switch_data.json', 'w') as json_file:
        json.dump(switch_data, json_file, indent=4)

    print("Switch data saved to switch_data.json")

if __name__ == "__main__":
    connected()
    ipconnecttest()
    jfile()
