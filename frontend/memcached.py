from pymemcache import serde
from pymemcache.client import base
import json
import time
import datetime
import random
import base64
import bz2
from datetime import timedelta
MC_ADDRESS = 'localhost'
MC_PORT = 11211
PCS_KEY = 'pcs'


class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return JsonSerde.compress(JsonSerde.endoceBase64(value)), 1
        return JsonSerde.compress(JsonSerde.endoceBase64(json.dumps(value))), 2

    def deserialize(self, key, value, flags):
        value = JsonSerde.decodeBase64(JsonSerde.decompress(value))
        if flags == 1:
            return value
        if flags == 2:
            return json.loads(value)
        raise Exception("Unknown serialization format")

    def endoceBase64(msg):
        encodedBytes = base64.b64encode(msg.encode("utf-8"))
        return str(encodedBytes, "utf-8")

    def decodeBase64(msg):
        decodedBytes = base64.b64decode(msg)
        return str(decodedBytes, "utf-8")

    def compress(msg):
        return bz2.compress(msg.encode('utf-8'))

    def decompress(data):
        return bz2.decompress(data).decode('utf-8')


class Cache:
    def __init__(self):
        self._client = Cache.getMemcachedClient()

    def getMemcachedClient():
        print(
            f"connecting to memcached at: {MC_ADDRESS}:{MC_PORT} ... ", end="")
        client = base.Client((MC_ADDRESS, MC_PORT),  serde=serde.pickle_serde)
        # client.cache_memlimit(1024)
        # print(client.stats())
        print("success")
        return client

    def generate_sample_data(self):
        def generate_pc_info(pcname):
            currentDatetimeIso = datetime.datetime.utcnow().isoformat()
            data = {
                "pcname": pcname,
                "time": currentDatetimeIso,
                "system": {
                    "system": "Windows",
                    "name": "ADAMKO-DM",
                    "version": "10.0.22000",
                    "machine": "AMD64",
                    "boot": "2022/1/16 13:41:38"
                },
                "cpu": {
                    "cores": 4,
                    "logical_cores": 8,
                    "usage": {
                        "0": random.randrange(15, 35, 1),
                        "1": random.randrange(15, 35, 1),
                        "2": random.randrange(15, 35, 1),
                        "3": random.randrange(15, 35, 1),
                        "4": random.randrange(15, 35, 1),
                        "5": random.randrange(15, 35, 1),
                        "6": random.randrange(15, 35, 1),
                        "7": random.randrange(15, 35, 1)
                    },
                    "total": random.randrange(20, 40, 1)
                },
                "memory": {
                    "total": 32*1024,
                    "available": 16*1024,
                    "used": random.randrange(3, 5)*1024
                },
                "gpus": [
                    {
                        "id" : 0,
                        "name" :"example gpu",
                        "load" :random.randrange(5, 35),
                        "temp" : random.randrange(55, 105),
                        "memory": {
                            "total": 6*1024,
                            "used": random.randrange(1, 4)*1024
                        },
                    }
                ]
            }
            return data
        # self._client.flush_all()
        sample_pcs = [f'example-pc-{i}' for i in range(3)]
        self._client.set(PCS_KEY, sample_pcs)
        # generate sample data
        for pc in sample_pcs:
            pc_data_keys = []
            for i in range(11_000):
                date = datetime.datetime.utcnow() - timedelta(minutes=i)
                key = f"{pc}/{date.isoformat()}"
                pc_data_keys.append(key)
                data = generate_pc_info(pc)
                data['time'] = date.isoformat()
                self._client.set(key, data)
            self._client.set(pc, pc_data_keys)

    def get_pcs(self):
        return self._client.get(PCS_KEY)

    def get_pc_keys(self, pcname):
        return self._client.get(pcname)
    
    def get_pc_data_latest_entry(self, pcname):
        keys = self._client.get(pcname)
        if keys:
            if len(keys) > 0:
                key = keys[len(keys)-1]
                result = self._client.get(key)
                return result
        return {}

    def get_pc_data(self, pcname, fromLastHours=1):
        keys = self._client.get(pcname)
        n = datetime.datetime.utcnow()
        d = timedelta(hours=fromLastHours, minutes=0)
        fromDatetime = n - d

        keys = list(filter(lambda x:
                           datetime.datetime.fromisoformat(x.split('/')[1]) > fromDatetime, keys))

        chunk_size = 200
        chunked_keys = [keys[i:i+chunk_size]
                        for i in range(0, len(keys), chunk_size)]
        result = {}
        for chunk in chunked_keys:
            result = {**result, **self._client.get_many(chunk)}
        return result
