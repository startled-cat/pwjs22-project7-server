
from flask import Flask, Response, make_response, redirect, render_template, request, send_file, url_for
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import memcached as mc
import pandas as pd

PORT = int(os.environ.get('PORT', 8080))

app = Flask(__name__)

resource_types = ['cpu_load', 'mem_load',
                  'gpu_load', 'gpu_temp', 'gpu_mem_load']


def handleJsonResponse(data):
    return Response(json.dumps(data),  mimetype='application/json')


@app.route('/pc', methods=['GET'])
def get_pcs():
    cache = mc.Cache()
    return handleJsonResponse(cache.get_pcs())


@app.route('/pc/<pcname>', methods=['GET'])
def get_pc_by_name(pcname):
    cache = mc.Cache()
    return handleJsonResponse(cache.get_pc_keys(pcname))


@app.route('/pc/<pcname>/<int:lasthours>', methods=['GET'])
def get_pc_dataEntries(pcname, lasthours):
    cache = mc.Cache()
    return handleJsonResponse(cache.get_pc_data(pcname, lasthours))


@app.route('/pc/<pcname>/<int:lasthours>/graph/<resourcetype>', methods=['GET'])
def get_pc_graph(pcname, lasthours, resourcetype=resource_types[0]):

    cache = mc.Cache()
    data = cache.get_pc_data(pcname, lasthours)

    graphFilename = f'img/{pcname}_{resourcetype}_-{lasthours}h.png'

    dataList = list(data.items())
    systemInfoEntries = [x[1] for x in dataList]

    timestamps = [datetime.strptime(x['time'][0:19].replace(
        "T", " "), '%Y-%m-%d %H:%M:%S') for x in systemInfoEntries]
    dates = [datetime.strptime(f"{x['time'][0:10]}T00:00:00".replace(
        "T", " "), '%Y-%m-%d %H:%M:%S') for x in systemInfoEntries]
    dates_h = [datetime.strptime(f"{x['time'][0:13]}:00:00".replace(
        "T", " "), '%Y-%m-%d %H:%M:%S') for x in systemInfoEntries]
    # times = [x['time'][10:15] for x in systemInfoEntries]

    df = pd.DataFrame(
        {
            'timestamp': timestamps,
            'date': dates,
            'date_h': dates_h,
            # 'time':times,
            resource_types[0]: [x['cpu']['total'] for x in systemInfoEntries],
            resource_types[1]: [(x['memory']['used'] / x['memory']['total'])*100 for x in systemInfoEntries],
            resource_types[2]: [x['gpus'][0]['load'] for x in systemInfoEntries],
            resource_types[3]: [x['gpus'][0]['temp'] for x in systemInfoEntries],
            resource_types[4]: [x['gpus'][0]['memory']['used'] / x['gpus'][0]['memory']['total'] for x in systemInfoEntries],
        })

    fig, ax = plt.subplots()
    fig.autofmt_xdate()
    unit = ''
    duration = ''

    if lasthours < 24:
        duration = f"{lasthours}h"
    else:
        duration = f"{lasthours//24}d"

    if 'temp' in resourcetype:
        unit = '[C]'
    if 'load' in resourcetype:
        ax.set_ylim(0, 100)
        unit = '[%]'

    ax.set(xlabel='', ylabel=f'{resourcetype} {unit}',
           title=f'{resourcetype} of {pcname} in last {duration}')

    if len(df) > 1000:
        df = df.groupby('date_h').mean().reset_index()
        ax.plot(df['date_h'], df[resourcetype])
    else:
        ax.plot(df['timestamp'], df[resourcetype])

    ax.grid()

    if lasthours < 24:
        xfmt = mdates.DateFormatter('%H:%M')
    else:
        xfmt = mdates.DateFormatter('%m-%d %H:%M')

    ax.xaxis.set_major_formatter(xfmt)

    plt.savefig(graphFilename)
    return send_file(graphFilename, mimetype='image/png')


@app.route('/cache/populate', methods=['GET'])
def populate_cache():
    cache = mc.Cache()
    cache.generate_sample_data()
    return '', 200
    
    
@app.route('/cache/clear', methods=['GET'])
def clear_cache():
    cache = mc.Cache()
    cache._client.flush_all()
    cache._client.set(mc.PCS_KEY, [])
    return '', 200


@app.route('/', methods=['GET'])
def get_index():
    cache = mc.Cache()
    pc = request.args.get("pc")
    view = request.args.get("view", 1, type=int)
    resource = request.args.get("resource", resource_types[0])
    all_pcs = cache.get_pcs()
    if all_pcs is None:
        all_pcs = []
        
    print(f" pc = {pc}")
    if pc:
        pc_info = cache.get_pc_data_latest_entry(pc)
    else:
        pc_info = {}
    

    return render_template('index.html', all_pcs=all_pcs, pc=pc, pc_info=pc_info, view=view, resource=resource, resource_types=resource_types)


if __name__ == '__main__':
    app.run(port=PORT)
    app.add_url_rule('/favicon.ico',
                     redirect_to=url_for('static', filename='favicon.ico'))
    app.add_url_rule('/icon.png',
                     redirect_to=url_for('static', filename='icon.png'))
