#!/usr/bin/env python3

from flask import Flask, render_template
from flask_socketio import SocketIO
import time
import threading

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
    thread = threading.Thread(target=count_and_emit)
    thread.start()
    socketio.run(app, host='0.0.0.0', port=5000)
