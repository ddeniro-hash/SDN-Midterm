#!/usr/bin/env python3

from flask import Flask, render_template
from flask_socketio import SocketIO
import time
import threading
from netmiko import ConnectHandler
import paramiko
import sshinfo
import re
import time
import os
import shutil
import subprocess

r1_username, r1_password, r1_ip = sshinfo.get_device_info("R1")
r2_username, r2_password, r2_ip = sshinfo.get_device_info("R2")
r3_username, r3_password, r3_ip = sshinfo.get_device_info("R3")

# Print statment to show Json data *** TROUBLESHOOTING ****
'''print("R1 Details:")
print(f"  Username: {r1_username}, Password: {r1_password}, IP: {r1_ip}")
print("R2 Details:")
print(f"  Username: {r2_username}, Password: {r2_password}, IP: {r2_ip}")
print("R3 Details:")
print(f"  Username: {r3_username}, Password: {r3_password}, IP: {r3_ip}")'''

def getdhcpbinding():
    R1 = { # Router 1 information used in the connecthandler part
    'device_type': 'cisco_ios',
    'host': r1_ip,
    'username': r1_username,
    'password': r1_password,
    'secret': r1_password,
    }
    net_connect = ConnectHandler(**R1)
    net_connect.enable()
    config = "do show ip dhcp binding"
    data = net_connect.send_config_set(config)
    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', data)
    # Troubleshooting ****
    # print(data)
    '''if match:
        print(f"IP Address R1: {match.group(1)}")
    else:
        print("No IP Address found.")'''
    return(match.group(1))

def configure_mininet(controller_ip="10.20.30.2"):
    ip_mininet = getdhcpbinding()
    print(f"IP address for mininetVM: {ip_mininet}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)

    try:
        ssh.connect(hostname=ip_mininet, username='mininet', password='mininet')
        print(f"Connected to {ip_mininet}")

        # Start Mininet in a Tmux session
        tmux_command = "sudo -S tmux new-session -d -s mininet-session 'mn --switch=ovsk,protocols=OpenFlow13'"
        stdin, stdout, stderr = ssh.exec_command(tmux_command, get_pty=True)
        stdin.write('mininet\n')  # Provide sudo password
        stdin.flush()
        time.sleep(5)
        print("Mininet is now running in a Tmux session.")

        # Attach to tmux session and execute Mininet command
        attach_command = "tmux attach-session -t mininet-session"
        stdin, stdout, stderr = ssh.exec_command(attach_command, get_pty=True)

        # Send Mininet command
        mininet_command = "py s1.attach('eth0')\n"
        stdin.write(mininet_command)
        stdin.flush()
        time.sleep(2)  # Allow command to execute

        # Set controller IP for s1
        ovs_command = f"sudo -S ovs-vsctl set-controller s1 tcp:{controller_ip}:6653"
        stdin, stdout, stderr = ssh.exec_command(ovs_command, get_pty=True)
        stdin.write('mininet\n')  # Provide sudo password
        stdin.flush()
        print(f"Controller IP successfully changed to {controller_ip}.")
    
        time.sleep(10)

        ovs2_command = f"sudo -S ovs-vsctl show"
        stdin, stdout, stderr = ssh.exec_command(ovs2_command, get_pty=True)
        stdin.write('mininet\n')  # Provide sudo password
        stdin.flush()
        output = stdout.read().decode()
        error = stderr.read().decode()
        if output:
            print(f"Output:\n{output}")
        if error:
            print(f"Error:\n{error}")
            
    except Exception as e:
        print(f"Connection or command failed: {e}")
    
    ssh.close()
    print("SSH (R1) connection closed.")

def routerconfigs():
    R1 = { # Router 1 information used in the connecthandler part
    'device_type': 'cisco_ios',
    'host': r1_ip,
    'username': r1_username,
    'password': r1_password,
    'secret': r1_password,
    }
    R2 = { # Router 2 information used in the connecthandler part
    'device_type': 'cisco_ios',
    'host': r2_ip,
    'username': r2_username,
    'password': r2_password,
    'secret': r2_password,
    }
    R3 = { # Router 3 information used in the connecthandler part
    'device_type': 'cisco_ios',
    'host': r3_ip,
    'username': r3_username,
    'password': r3_password,
    'secret': r3_password,
    }

    #routers = [R1, R2, R3]

    try:
        net_connectr1 = ConnectHandler(**R1)
        net_connectr1.enable()
        contentr1 = net_connectr1.send_config_from_file("/home/netman/Documents/midterm/r1config.txt")
        #print(contentr1)
        net_connectr1.disconnect()
        print("R1 have been configured!")
    except:
        print("R1 was not configured. Check commands and ssh connection.")
    
    try:
        net_connectr2 = ConnectHandler(**R2)
        net_connectr2.enable()
        contentr2 = net_connectr2.send_config_from_file("/home/netman/Documents/midterm/r2config.txt")
        #print(contentr2)
        net_connectr2.disconnect()
        print("R2 have been configured!")
    except:
        print("R2 was not configured. Check commands and ssh connection.")
    
    try:
        net_connectr3 = ConnectHandler(**R3)
        net_connectr3.enable()
        contentr3 = net_connectr3.send_config_from_file("/home/netman/Documents/midterm/r3config.txt")
        #print(contentr3)
        net_connectr3.disconnect()
        print("R3 have been configured!")
    except:
        print("R3 was not configured. Check commands and ssh connection.")
    
def gitpush():
    source1 = "/home/netman/Documents/flask_openflow"
    source2 = "/home/netman/Documents/midterm"
    destination = "/home/netman/Documents/gitpushmidterm"
    username = "ddeniro-hash"
    token = "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"

    shutil.copytree(source1, os.path.join(destination, "flask_openflow"), dirs_exist_ok=True)
    shutil.copytree(source2, os.path.join(destination, "midterm"), dirs_exist_ok=True)
    print("Directories copied successfully.")

    os.chdir(destination)

    subprocess.run(["git", "init"], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "initial commit"], check=True)
    subprocess.run(["git", "remote", "remove", "origin"], check=True)
    remote_url = f"https://{token}@github.com/{username}/SDN-Midterm.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
    subprocess.run(["git", "push", "-u", "origin", "master"], check=True)

app = Flask(__name__)
socketio = SocketIO(app)

file_path = '/home/netman/Documents/flask_openflow/cap.txt'  # Path to your packet capture file

def count_openflow_messages(file_path):
    with open(file_path, 'r') as f:
        data = f.readlines()
    
    # Count all OpenFlow messages
    count = sum(1 for line in data if "OpenFlow" in line)  # Adjust this line to match the format of your OpenFlow messages
    return count

def count_and_emit():
    while True:
        count = count_openflow_messages(file_path)
        socketio.emit('openflow_message_count', {'count': count})
        time.sleep(5)  # Wait for 5 seconds before next count

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    getdhcpbinding()
    routerconfigs()
    configure_mininet()
    gitpush()
    thread = threading.Thread(target=count_and_emit)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000)
