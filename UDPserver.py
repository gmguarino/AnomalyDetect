#! /usr/bin/python3

import socket
import multiprocessing
import threading
import time
import sys
from AD import iterative_remover, als_baseline
import numpy as np
from scipy.signal import medfilt
import json


class UDPConnect(threading.Thread):

    def __init__(self, queue, host, port=44444, buffer=1024, verbose=0):
        super().__init__()
        self.host = host
        self.port = port
        self.buffer = buffer
        self.socket = None
        self.q = queue
        self._stop_flag = threading.Event()
        self.verbose = verbose

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        return self.socket

    def stop(self):
        if not self._stop_flag.isSet():
            self._stop_flag.set()
            self.socket.close()
            print(f"\n Closed socket connection from {self.host} on port {self.port}")
            # sys.exit()

    def stop_status(self):
        return self._stop_flag.isSet()

    @staticmethod
    def parse_data_string(data):
        data_list = data.split(',')
        value = float(data_list[0])
        time = int(data_list[1])
        anomaly = int(data_list[2])
        return [value, time, anomaly]

    def run(self):
        print("Starting UDP reception")
        while True:
            if self.stop_status():
                print("Detected Stop")
                return
            try:
                data = self.socket.recvfrom(self.buffer)

                if data:
                    value, time, anomaly = UDPConnect.parse_data_string(data[0].decode('utf-8'))
                    self.q.put([value, time, anomaly])
                    if self.verbose > 0:
                        print("Client to Server: ", data)
                        print(f"Value: {value}; time (millis): {time}; anomaly: {anomaly}({bool(anomaly)})")
                    self.socket.sendto((str(value * -1) + ',' + str(time)).encode('utf-8'), data[1])
            except (KeyboardInterrupt, OSError):
                self.stop()
                break


class Consumer(threading.Thread):

    def __init__(self, queue, limit=500, step_size=100):
        super().__init__()
        self.q = queue
        self.data = {'values': [], 'times': [], 'anomaly': []}
        self._stop_flag = threading.Event()
        self.limit = limit
        self.count = 0
        self.step_size = step_size
        print("Consumer Initialised")

    def stop(self):
        if not self._stop_flag.isSet():
            self._stop_flag.set()

    def stop_status(self):
        return self._stop_flag.isSet()

    def elaborate(self):
        baseline = als_baseline(np.asarray(self.data['values']), lam=1e2, p=0.15, niter=10)
        detrended = np.asarray(self.data['values']) - baseline
        remainder, season = iterative_remover(detrended, decimation_rate=0.8)
        self.data['season'] = list(season.flatten())
        self.data['remainder'] = list(remainder.flatten())
        self.data['baseline'] = list(baseline.flatten())
        with open('test.json', 'w+') as f:
            json.dump(self.data, f)
        self.stop()

    def parse_data(self, data):
        for idx, key in enumerate(self.data):
            self.data[key].append(data[idx])
        self.count += 1
        if self.count >= self.limit:
            self.elaborate()
            self.count -= self.step_size

    def run(self):
        count = 0
        while True:
            if self.stop_status():
                print("Consumer Stopped")
                return
            count += 1

            data = self.q.get()
            if data is None:
                break
            else:
                self.parse_data(data)
            print(count, self.count, "...", end=' ')

            print(data)


def main():
    q = multiprocessing.Queue()
    running = False
    host = "192.168.4.1"

    port = 44444

    buffer = 1024
    connection = UDPConnect(q, host, port, buffer, verbose=0)
    connection.connect()
    connection.start()
    consumer = None
    while True:
        try:
            time.sleep(0.1)
            if running is not True:
                consumer = Consumer(q)
                consumer.start()
                running = True
            if consumer.stop_status() or connection.stop_status():
                connection.stop()

                if consumer:
                    consumer.stop()
                    break
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
            connection.stop()
            print("Connection stop main")

            if consumer:
                consumer.stop()
            break


main()
# connection.run(verbose=0)

# skt = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
# skt.bind((host, port))
#
# while True:
#
#     try:
#         data = skt.recvfrom(buffer)
#
#         if data:
#             print("Client to Server: ", data)
#             skt.sendto(data[0], data[1])
#     except KeyboardInterrupt:
#         skt.close()
#         print(f"Closed socket connection from {host} on port {port}")
#         exit()
