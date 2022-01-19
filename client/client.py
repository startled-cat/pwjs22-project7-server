import psutil
import GPUtil
import platform
import sys
from datetime import datetime
import time
import memcached as mc

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
    systemInfo = {'system': uname.system,
                  'name': uname.node,
                  'version': uname.version,
                  'machine': uname.machine,
                  'boot': boot_t}

    ######################## CPU information ######################
    cpufreq = psutil.cpu_freq()

    coresInfo = {}
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        coresInfo[i] = percentage

    cpuInfo = {'cores': psutil.cpu_count(logical=False),
               'logical_cores': psutil.cpu_count(logical=True),
               'usage': coresInfo,
               'total': psutil.cpu_percent()}

    ########################## Memory Information ##############################
    svmem = psutil.virtual_memory()

    memoryInfo = {'total': get_size(svmem.total),
                  'available': get_size(svmem.available),
                  'used': get_size(svmem.used)}

    ########################################################

    gpus = []
    for gpu in GPUtil.getGPUs():
        gpu_id = gpu.id
        gpu_name = gpu.name
        gpu_load = gpu.load
        gpu_used_memory = gpu.memoryUsed
        gpu_total_memory = gpu.memoryTotal
        gpu_temperature = gpu.temperature

        gpus.append({
            'id': gpu_id,
            'name': gpu_name,
            'load': gpu_load,
            'temp': gpu_temperature,
            'memory': {
                'total': gpu_total_memory,
                'used': gpu_used_memory
            }
        })

    data = {'system': systemInfo,
            'cpu': cpuInfo,
            'memory': memoryInfo,
            'gpus': gpus}

    # with open('data.txt', 'w') as outfile:
    # json.dump(data, outfile)

    # print(data)
    return data
#######################################################


if __name__ == '__main__':
    MC_ADDRESS = 'localhost'
    MC_PORT = 11211
    PC_KEY = platform.uname().node
    pc_data_keys = []
    loppForEver = False
    sleepFor = 0

    print(f"pc name: {PC_KEY}")

    cache = mc.Cache()

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


    

    while True:
        data = getPcStats()
        cache.add_pc(PC_KEY)
        data = cache.add_stats(PC_KEY, data)
        print(f"memcached key: {data['key']}")

        if not loppForEver:
            break

        time.sleep(sleepFor)
