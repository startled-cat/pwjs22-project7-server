MC_ADDRESS = 'localhost'
MC_PORT = 11211
PCS_KEY = 'pcs'

def getMemcachedClient():
    from pymemcache.client import base
    print(f"connecting to memcached at: {MC_ADDRESS}:{MC_PORT} ... ", end="")
    client = base.Client((MC_ADDRESS, MC_PORT))
    assertConnection(client)
    print("success")
    return client

def assertConnection(client):
    try:
        client.stats()
    except Exception as e:
        import sys
        print(f"could not connect")
        print(e)
        sys.exit(1)