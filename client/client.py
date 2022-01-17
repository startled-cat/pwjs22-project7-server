import psutil
import platform
import sys
from datetime import datetime
import json
from pymemcache import serde
from pymemcache.client import base
import time


class JsonSerde(object):
	def serialize(self, key, value):
		if isinstance(value, str):
			return value, 1
		return json.dumps(value), 2

	def deserialize(self, key, value, flags):
		if flags == 1:
	   		return value
		if flags == 2:
	   		return json.loads(value)
		raise Exception("Unknown serialization format")

######################################################################
def get_size(bytes, suffix="B"):
    return bytes
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor

def getPcStats():
################# SYSTEM INFO #################
	uname = platform.uname()

	# Boot Time
	boot_time_timestamp = psutil.boot_time()
	bt = datetime.fromtimestamp(boot_time_timestamp)

	boot_t = f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"
	systemInfo =    {'system' : uname.system,
		        'name' : uname.node,
		        'version' : uname.version,
		        'machine' : uname.machine,
		        'boot' : boot_t}


	######################## CPU information ######################
	cpufreq = psutil.cpu_freq()

	coresInfo = {}
	for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
	    coresInfo[i] = percentage 

	cpuInfo =  {'cores' : psutil.cpu_count(logical=False),
		    'logical_cores' : psutil.cpu_count(logical=True),
		    'usage' : coresInfo, 
		    'total' : psutil.cpu_percent()}


	########################## Memory Information ##############################
	svmem = psutil.virtual_memory()

	memoryInfo = {'total' : get_size(svmem.total),
		      'available' : get_size(svmem.available),
		      'used' : get_size(svmem.used)}

	########################################################
	data = {'system' : systemInfo,
		'cpu' : cpuInfo,
		'memory' : memoryInfo}
		
	#with open('data.txt', 'w') as outfile:
	   # json.dump(data, outfile)



	#print(data)
	return data
#######################################################

    
def getMemcachedClient():
		print(f"connecting to memcached at: {MC_ADDRESS}:{MC_PORT} ... ", end="")
		client = base.Client((MC_ADDRESS, MC_PORT),  serde=serde.pickle_serde)
		# client.cache_memlimit(1024)
		# print(client.stats())
		print("success")
		return client
		

if __name__ == '__main__':
	MC_ADDRESS = 'localhost'
	MC_PORT = 11211
	PC_KEY = 'pc-3'
	pc_data_keys = []
	loppForEver = False
	sleepFor = 0

	
	try:
		arg = sys.argv[1]
		if arg.isnumeric():
			loppForEver = True
			sleepFor = int(arg)
		else:
			print('Niepoprawny argument!')
			sys.exit()
	except:
		pass


	client = getMemcachedClient()
	
	while True:

		if client.get(PC_KEY) is not None:
			pc_data_keys = client.get(PC_KEY)

		date = datetime.utcnow()
		key = f"{PC_KEY}/{date.isoformat()}"
		pc_data_keys.append(key)
		data = getPcStats()
		data['time'] = date.isoformat()

		client.set(key, data)
		client.set(PC_KEY, pc_data_keys)
		print(key)

		if not loppForEver:
			break
			
		time.sleep(sleepFor)
		

