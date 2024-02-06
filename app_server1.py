
from flask import Flask, render_template, request
from flask_socketio import SocketIO, disconnect
from flask_cors import CORS

import time
import asyncio
import requests
import json

import numpy as np
from threading import Thread, Lock, Event


app = Flask(__name__)
CORS(app, resources={r"/socket.io/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*")

# 视频帧弄成全局变量，只用开一个线程
frame_lock = Lock()
frame_bytes = None

# 客户端线程
client_threads = {}
client_flags = {}


@socketio.on('connect', namespace='/video_stream')
def handle_connect():
    client_id = request.sid
    for id in client_threads:
        print(id)
        print(client_threads[id].is_alive())
    print(f'Client {client_id} connected')

    if client_id not in client_threads or not client_threads[client_id].is_alive():
        client_flags[client_id] = True
        client_threads[client_id] = Thread(target=emit_thread, args=(client_id,))
        client_threads[client_id].stop_event = Event()
        client_threads[client_id].daemon = True
        client_threads[client_id].start()
    #socketio.emit('video_frame', {'image': frame_bytes}, namespace='/video_stream')


@socketio.on('disconnect', namespace = '/video_stream')
def handle_disconnect():
	client_id = request.sid
	print(f'Client {client_id} disconnected')
	disconnect()

	if client_id in client_threads and client_threads[client_id].is_alive():
		#print("loose thread")
		client_flags[client_id] = False
		client_threads[client_id].stop_event.set()
		#client_threads[client_id]._stop()
		client_threads[client_id].join()
		del client_threads[client_id]
		del client_flags[client_id]

@socketio.on('send_barrage', namespace='/video_stream')
def handle_barrage(data, namespace):
	message = data['message']
	print('receive barrage')
	print(f"Received barrage from client: {message}")

	socketio.emit('broadcast_barrage', {'message':message}, namespace='/video_stream')
	time.sleep(8)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='xxxxxxxx', port=5000)

