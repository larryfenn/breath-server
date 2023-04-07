# export FLASK_APP=app

# todo:
# better data visualization
# stylesheets (?)
# a standalone "status"/analytics page?
# favicon
# what to do with title page

import sys
from flask import Flask, Response
from flask import request
from flask import g
from flask import Response
import sqlite3
from datetime import datetime
from pytz import timezone
from io import BytesIO
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

DATABASE = 'data/data.sqlite'
app = Flask(__name__)

def create_app():
    return app

# this will drop all data that might exist in the db
# for ex. if run like
# > python3
# >>> from app import init_db
# >>> init_db()
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def frontpage():
    return """
<!doctype html>
<html>
  <head>
    <style>
     .flex-container {
       display: flex;
       flex-wrap: wrap;
     }
    </style>
    <title>
      Breath Server
    </title>
  </head>
  <body>
    <div class="flex-container" >
      <div>
        <img src="/rco2.png"/>
      </div>
      <div>
        <img src="/atmp.png"/>
      </div>
      <div>
        <img src="/rhum.png"/>
      </div>
      <div>
        <img src="/pm02.png"/>
      </div>
      <div>
        <img src="/tvoc_index.png"/>
      </div>
      <div>
        <img src="/nox_index.png"/>
      </div>
    </div>
  </body>
</html>
"""

@app.route("/sensor", methods=['GET'])
def sensor():
    return get_relay_state()

@app.route("/sensors/8a93c7", methods=['POST'])
def sensors_8a93c7():
    sensor_data = dict()
    sensor_data['id'] = '8a93c7'
    sensor_data['rco2'] = int(request.json['rco2'])
    sensor_data['pm02'] = int(request.json['pm02'])
    sensor_data['tvoc_index'] = int(request.json['tvoc_index'])
    sensor_data['nox_index'] = int(request.json['nox_index'])
    sensor_data['atmp'] = float(request.json['atmp'])
    sensor_data['rhum'] = int(request.json['rhum'])
    return log_data(sensor_data, control = True)

@app.route("/sensors/dd58e7", methods=['POST'])
def sensors_dd58e7():
    sensor_data = dict()
    sensor_data['id'] = 'dd58e7'
    sensor_data['rco2'] = int(request.json['rco2'])
    sensor_data['pm02'] = int(request.json['pm02'])
    sensor_data['tvoc_index'] = int(request.json['tvoc_index'])
    sensor_data['nox_index'] = int(request.json['nox_index'])
    sensor_data['atmp'] = float(request.json['atmp'])
    sensor_data['rhum'] = int(request.json['rhum'])
    return log_data(sensor_data, control = False)

def log_data(data, control):
    db = get_db()
    db.execute(
        'INSERT INTO air_quality_log (id, rco2, pm02, tvoc_index, nox_index, atmp, rhum) \
         VALUES (?, ?, ?, ?, ?, ?, ?)',
        (
            data['id'],
            data['rco2'],
            data['pm02'],
            data['tvoc_index'],
            data['nox_index'],
            data['atmp'],
            data['rhum']
        ))
    db.commit()
    if control:
        set_relay_state(data)
    return get_relay_state()

def set_relay_state(data):
    # first check override; no need to do anything if override is on
    override = query_db(
        'SELECT max(time), override \
           FROM state', one = True)['override']
    if override > 0:
        return
    # Relay on logic goes here:
    relay_on = False
    if data['pm02'] > 5:
        relay_on = True


    # End relay logic
    if relay_on:
        db = get_db()
        db.execute(
            'INSERT INTO state (override, relay_state) \
             VALUES (0, 1)'
        )
        db.commit()

def get_relay_state():
    state = query_db(
        'SELECT max(time), override, relay_state \
           FROM state', one = True)
    override = state['override']
    relay_on = state['relay_state']
    if(override == 0):
        if(relay_on):
            return "on"
        else:
            return "off"
    elif(override == 1):
        return "off"
    else:
        return "on"

@app.route("/control", methods = ['GET', 'POST'])
def control():
    state = query_db(
        'SELECT max(time), override, relay_state \
           FROM state', one = True)
    relay_state = state['relay_state']
    if request.method == 'POST':
        # read checkbox state and commit that as relay state
        override = int(request.form.get('override'))
        db = get_db()
        if override == 1:
            db.execute(
                'INSERT INTO state (override, relay_state) \
                 VALUES (1, 0)'
            )
        elif override == 2:
            db.execute(
                'INSERT INTO state (override, relay_state) \
                 VALUES (2, 1)'
            )
        else:
            db.execute(
                f'INSERT INTO state (override, relay_state) \
                  VALUES (0, {relay_state})'
            )
        db.commit()
    state = query_db(
        'SELECT max(time), override, relay_state \
           FROM state', one = True)
    override = state['override']
    relay_state = "On" if state['relay_state'] == 1 else "Off"

    bedroom_data = query_db(
        'SELECT max(time) as time, pm02, rco2 \
           FROM air_quality_log \
          WHERE id = "dd58e7"', one = True)
    main_room_data = query_db(
        'SELECT max(time) as time, pm02, rco2 \
           FROM air_quality_log \
          WHERE id = "8a93c7"', one = True)
    bedroom_time_formatted = timezone('UTC').localize(datetime.strptime(bedroom_data['time'], '%Y-%m-%d %H:%M:%S')).astimezone(timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    main_room_time_formatted = timezone('UTC').localize(datetime.strptime(main_room_data['time'], '%Y-%m-%d %H:%M:%S')).astimezone(timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    bedroom_data_formatted = f"{bedroom_time_formatted} PM 2.5: {bedroom_data['pm02']} CO2: {bedroom_data['rco2']}"
    main_room_data_formatted = f"{main_room_time_formatted} PM 2.5: {main_room_data['pm02']} CO2: {main_room_data['rco2']}"
    no_override = "checked" if override == 0 else ""
    override_off = "checked" if override == 1 else ""
    override_on = "checked" if override == 2 else ""
    page = f'''Last observation:<br>Bedroom: {bedroom_data_formatted}<br>Main room: {main_room_data_formatted}<br>
Current relay state: {relay_state}
<form method="post">
    <input type="radio" id="no_override" name="override" value="0" {no_override}>
    <label for="no_override">No Override</label><br>
    <input type="radio" id="override_off" name="override" value="1" {override_off}>
    <label for="no_override">Override Relay Off</label><br>
    <input type="radio" id="override_on" name="override" value="2" {override_on}>
    <label for="no_override">Override Relay On</label><br>
    <input type="submit" value="Submit">
</form>'''
    return page

@app.route("/rco2.png")
def rco2():
    return nocache(plot_response("rco2"))

@app.route("/atmp.png")
def atmp():
    return nocache(plot_response("atmp"))

@app.route("/rhum.png")
def rhum():
    return nocache(plot_response("rhum"))

@app.route("/pm02.png")
def pm02():
    return nocache(plot_response("pm02"))

@app.route("/tvoc_index.png")
def tvoc_index():
    return nocache(plot_response("tvoc_index"))

@app.route("/nox_index.png")
def nox_index():
    return nocache(plot_response("nox_index"))

def plot_response(metric):
    units = {
        'rco2': 'ppm',
        'pm02': 'μg/m³',
        'tvoc_index': 'Gas Index',
        'nox_index': 'Gas Index',
        'atmp': '°C',
        'rhum': '%'}
    con = sqlite3.connect("data/data.sqlite")
    data = pd.read_sql_query(f"SELECT time, id, {metric} AS metric FROM air_quality_log WHERE time > datetime('now', '-1 day')", con)
    data['time'] = pd.to_datetime(data['time'], utc=True)
    data['time'] = data.time.dt.floor('min')
    data['id'] = np.where(data['id'] == '8a93c7', 'Main', 'Bedroom')
    to_plot = data.groupby(['id', 'time']).agg({'metric': 'mean'})
    fig = Figure()
    ax = fig.add_subplot()
    for id, df in to_plot.groupby(level = 0):
        ax.plot(df.index.get_level_values('time').values,
                df['metric'],
                label = df.index.get_level_values('id').values[0])
        ax.set_title(f"{metric} ({units[metric]})", loc = 'left')
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M', tz = timezone("America/New_York")))
        ax.legend(frameon = True, loc = "best")
    img_bytes = BytesIO()
    FigureCanvas(fig).print_png(img_bytes)
    return Response(img_bytes.getvalue(), mimetype='image/png')

def nocache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
