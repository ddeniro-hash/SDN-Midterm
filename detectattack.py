import subprocess
import re
import time
from collections import defaultdict, deque

# Configuration
interface = "ens33"
filter_expression = 'tcp port 6653'
display_filter = 'openflow_v4.type == 10'
output_file = 'openflow_output.txt'
threshold = 100
check_interval = 5  # seconds
monitor_duration = 10  # seconds
controller_ip = "10.100.100.141"
controller_port = "6653"

# Function to run tshark and capture output
def run_tshark():
    command = [
        'sudo', 'tshark', '-i', interface,
        '-f', filter_expression,
        '-Y', display_filter,
        '-O', 'openflow_v4'
    ]
    
    with open(output_file, 'w') as f:
        process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE)
        return process

def block_ip(src_ip):
    print("Blocking IP: {}".format(src_ip))
    block_command = [
        'sudo', 'iptables', '-A', 'INPUT', '-s', src_ip,
        '-d', controller_ip, '-p', 'tcp', '--dport', controller_port, '-j', 'DROP'
    ]
    subprocess.run(block_command)

# Function to analyze output and check packet counts
def analyze_output():
    ip_count = defaultdict(int)
    packet_time = deque()  # Track timestamps of packets

    while True:
        # Read the output file and update counts
        with open(output_file, 'r') as f:
            for line in f:
                match = re.search(r'Src: (\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    src_ip = match.group(1)
                    current_time = time.time()
                    
                    # Record the timestamp of the packet
                    packet_time.append((src_ip, current_time))
                    ip_count[src_ip] += 1

                    # Remove timestamps older than the monitoring duration
                    while packet_time and packet_time[0][1] < current_time - monitor_duration:
                        old_ip, _ = packet_time.popleft()
                        ip_count[old_ip] -= 1
                        if ip_count[old_ip] == 0:
                            del ip_count[old_ip]

        # Check for IPs exceeding the threshold
        exceeded = False
        for ip, count in ip_count.items():
            if count > threshold:
                print("Warning: Source IP {} has exceeded the packet threshold with {} packets.".format(ip, count))
                block_ip(ip)
                exceeded = True

        if not exceeded:
            print("No IPs exceeded the threshold in the last {} seconds.".format(monitor_duration))

        # Print total packets every check_interval seconds
        print("Total packets captured in the last {} seconds: {}".format(monitor_duration, sum(ip_count.values())))

        time.sleep(check_interval)

def main():
    # Run tshark in a subprocess
    tshark_process = run_tshark()
    
    try:
        # Analyze output until the process is terminated
        analyze_output()
    finally:
        # Terminate tshark
        tshark_process.terminate()
        tshark_process.wait()

if __name__ == "__main__":
    main()
