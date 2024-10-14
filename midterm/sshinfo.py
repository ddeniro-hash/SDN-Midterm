#!/usr/bin/env python3

try:
    import json
except ImportError:
    print("Install required modules (json)")
    exit()

def get_device_info(device):
    """
    Retrieve the username, password, and IP address for a given device.
    """
    try:
        with open('/home/netman/Documents/midterm/sshinfo.json') as file:  # Open the JSON file
            data = json.load(file)  # Load the JSON data as a dictionary
            device_info = data[device]  # Extract the dictionary for the specified device
            username = device_info['username']
            password = device_info['password']
            ip_address = device_info['ip_address']

            return username, password, ip_address

    except KeyError:
        print(f"Key value is incorrect or missing for {device}!")
        exit()
    except FileNotFoundError:
        print("File does not exist!")
        exit()

if __name__ == "__main__":
    get_device_info()
