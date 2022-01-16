from flask import Flask, make_response, redirect, render_template, request, send_file
from flask_bootstrap import Bootstrap
import os
import json
import numpy as np

import matplotlib.pyplot as plt


PORT = int(os.environ.get('PORT', 8080))

app = Flask(__name__)
Bootstrap(app)


@app.route('/graph', methods=['GET'])
def get_store():
    graphFilename = 'graph.png'


    # Data for plotting
    t = np.arange(0.0, 2.0, 0.01)
    s = 1 + np.sin(2 * np.pi * t)

    fig, ax = plt.subplots()
    ax.plot(t, s)

    ax.set(xlabel='time (s)', ylabel='voltage (mV)',
        title='About as simple as it gets, folks')
    ax.grid()

    

    plt.savefig(graphFilename)
    return send_file(graphFilename, mimetype='image/png')


@app.route('/', methods=['GET'])
def get_index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=PORT)
