from pymemcache import serde
from pymemcache.client import base
import json
import time
import random
import base64
import bz2
from datetime import timedelta, datetime
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

    def get_pcs(self):
        return self._client.get(PCS_KEY)

    def get_pc_keys(self, pcname):
        return self._client.get(pcname)
    
    def add_pc(self, pcname):
        pcs = self._client.get(PCS_KEY)
        if pcs is None:
            pcs = []
        if pcname not in pcs:
            pcs.append(pcname)
            self._client.set(PCS_KEY, pcs)
        
    
    def add_stats(self, pcname, value):
        now_iso = datetime.utcnow().isoformat()
        key = f"{pcname}/{now_iso}"
        keys = self._client.get(pcname)
        if keys is None:
            keys = []
        if key not in keys:
            value['time'] = now_iso
            value['key'] = key
            keys.append(key)
            self._client.set(pcname, keys)
            self._client.set(key, value)
            return value
        