# -*- coding: utf-8 -*-

import time
import socket
import struct
import logging

import toml

from sys import version_info
from pymodbus.client.sync import ModbusSerialClient
from log import setup_logging

STX = 0x02
ETX = 0x03
BLANK = 0x20


def get_conf(conf_file_path='conf.toml'):
    """read toml conf file for latter use.


    :param conf_file_path: absolute path of conf file.
    :return:a dict contains configured infomation.
    """
    if version_info[0] == 3:
        with open(conf_file_path, encoding='utf-8') as conf_file:
            config = toml.loads(conf_file.read())
    else:
        with open(conf_file_path) as conf_file:
            config = toml.loads(conf_file.read())

    return config


conf = get_conf()
setup_logging(conf['log'])
log = logging.getLogger('ak_modbus')


class modbus:
    def __init__(self, conf):
        """
        inti modbus client
        :param conf: conf of modbus
        """
        self.modbus = ModbusSerialClient(conf['protocol'], port=conf['port'], baudrate=conf['baudrate'],
                                         bytesize=conf['bytesize'], stopbits=conf['stopbits'], parity=conf['parity'])

    def connect(self):
        """
        check status of modbus (True or False)
        :return: 
        """
        return self.modbus.connect()

    def recv(self, conf):
        """
        recv data from modbus PLC
        :param conf: 
        :return: 
        """

        data_dict = {}
        log.debug('query data from address:{}, count:{}, unit:{}'.format(conf['addr'], conf['count'], conf['unit']))
        try:

            data = self.modbus.read_holding_registers(int(conf['addr'], base=16), count=conf['count'],
                                                      unit=conf['unit'])
            unit_id = data.unit_id
            payload = data.registers

            data_dict.update({data.unit_id: data.registers})
        except Exception as e:

            log.error(e)

        return data_dict

    def close(self):
        self.modbus.close()


class AK:
    def __init__(self, conf):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def build(self, conf):
        """
        build ak_server
        :param conf: 
        :return: 
        """

        address = (conf['ip'], conf['port'])
        log.debug(address)
        self.socket.bind(address)
        self.socket.listen(5)

    def parse(self, data):
        """
        parse data to the format ak need
        :param data: 
        :return: 
        """

        for k, v in data.items():
            d = v

        length = len(d)
        fmt = ">2b4s3b%dHb" % length
        cmd = b'ARES'
        fault_status = 0x00

        buf = struct.pack(fmt, STX, BLANK, cmd, BLANK, fault_status, BLANK, *d, ETX)

        return buf

    def connect(self):
        self.connection, addr = self.socket.accept()
        log.debug(self.connection)
        log.debug(addr)

        return self.connection

    def recv_ak(self, connection):
        """
        recv ak protocol from ak_client
        :return: 
        """

        data = connection.recv(1024)
        log.debug('recv cmd : {}'.format(data))
        return data

    def send(self, data):
        """
        send data to  connect ak_client
        :return: 
        """
        self.connection.send(data)
        log.debug('send data to ak : {}'.format(data))


class Connections:
    def __init__(self, modbus, ak, modbus_conf, ak_conf):
        self.modbus = modbus
        self.ak = ak
        self.queue = []
        self.modbus_conf = modbus_conf
        self.ak_conf = ak_conf

    def query_modbus(self):
        """
        query modbus data
        """
        data = self.modbus.recv(self.modbus_conf)
        return data

    def send_to_ak(self, modbus_data):
        """
        send modbus data to client
        :param modbus_data: 
        :return: 
        """
        self.ak.send(modbus_data)

    def run(self):

        # build server on ip, port
        self.ak.build(self.ak_conf)

        while True:
            # ready to accept client data
            conn = self.ak.connect()
            log.debug(conn)
            # recved conn
            while True:
                try:
                    log.debug('ready to recv data!')
                    data = self.ak.recv_ak(conn)
                    if data:
                        log.debug("recved AK cmd")
                        self.queue.append(data)

                    if self.queue:
                        self.queue.pop(-1)
                        modbus_data = self.query_modbus()
                        modbus_data_handle = self.ak.parse(modbus_data)
                        self.send_to_ak(modbus_data_handle)

                except Exception as e:

                    log.error(e)


def main():
    mod = modbus(conf['modbus'])
    ak = AK(conf['ak'])

    coon = Connections(mod, ak, conf['modbus'], conf['ak'])
    coon.run()


if __name__ == '__main__':
    main()
