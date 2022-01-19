
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

pcs = ['pc1', 'pc2', 'pc3']


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
def get_pc_graph(pcname, lasthours, resourcetype='cpu'):
    if resourcetype is None:
        resourcetype = 'cpu'
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
            'date':dates,
            'date_h':dates_h,
            # 'time':times,
            'cpu': [x['cpu']['total'] for x in systemInfoEntries],
            'mem': [(x['memory']['used'] / x['memory']['total'])
                    * 100 for x in systemInfoEntries]
        })
    
    fig, ax = plt.subplots()
    fig.autofmt_xdate()
    ax.set_ylim(0, 100)
    ax.set(xlabel='time', ylabel=f'{resourcetype} usage (%)',
           title=f'Total {resourcetype} usage of {pcname}')
    
    if len(df) > 100:
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


@app.route('/', methods=['GET'])
def get_index():
    cache = mc.Cache()
    pc = request.args.get("pc")
    view = request.args.get("view", 1, type=int)
    resource = request.args.get("resource", "cpu")
    all_pcs = cache.get_pcs()

    return render_template('index.html', all_pcs=all_pcs, pc=pc, view=view, resource=resource)


if __name__ == '__main__':
    cache = mc.Cache()
    cache.generate_sample_data()

    app.run(port=PORT)
    app.add_url_rule('/favicon.ico',
                     redirect_to=url_for('static', filename='favicon.ico'))
    app.add_url_rule('/icon.png',
                     redirect_to=url_for('static', filename='icon.png'))
