# export FLASK_APP=app

# todo:
# better data visualization
# stylesheets (?)
# a standalone "status"/analytics page?
# favicon
# what to do with title page

from flask import Flask, send_file
from flask import request
from flask import g
from flask import Response
import sqlite3
from datetime import datetime
from pytz import timezone
from io import BytesIO
import pandas as pd
import matplotlib.backends.backend_agg as backend
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
<head><title>Breath Server</title></head>
<body>
<div>
<img src="/scd_co2.png"/>
</div>
<div>
<img src="/scd_temp.png"/>
</div>
<div>
<img src="/scd_hum.png"/>
</div>
<div>
<img src="/bme_temp.png"/>
</div>
<div>
<img src="/bme_hum.png"/>
</div>
<div>
<img src="/bme_pressure.png"/>
</div>
<div>
<img src="/bme_gas.png"/>
</div>
<div>
<img src="/pm25_env.png"/>
</div>
<div>
<img src="/aq_25um.png"/>
</div>
</body>
</html>
"""

@app.route("/sensor", methods=['GET', 'POST'])
def sensor():
    if request.method == 'POST':
        if valid_password(request.form['password']):
            sensor_data = dict()
            sensor_data['scd_co2'] = float(request.form['scd_co2'])
            sensor_data['scd_temp'] = float(request.form['scd_temp'])
            sensor_data['scd_hum'] = float(request.form['scd_hum'])
            sensor_data['bme_temp'] = float(request.form['bme_temp'])
            sensor_data['bme_gas'] = float(request.form['bme_gas'])
            sensor_data['bme_hum'] = float(request.form['bme_hum'])
            sensor_data['bme_pressure'] = float(request.form['bme_pressure'])
            sensor_data['pm25_env'] = int(request.form['pm25_env'])
            sensor_data['aq_25um'] = int(request.form['aq_25um'])
            return log_data(sensor_data)
        else:
            return Response(response = "Wrong password", status = "401")
    return get_relay_state();

def valid_password(password):
    return password == "fuck"

def log_data(data):
    db = get_db()
    db.execute(
        'INSERT INTO air_quality_log (scd_co2, scd_temp, scd_hum, bme_temp, bme_gas, bme_hum, bme_pressure, pm25_env, aq_25um) \
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            data['scd_co2'],
            data['scd_temp'],
            data['scd_hum'],
            data['bme_temp'],
            data['bme_gas'],
            data['bme_hum'],
            data['bme_pressure'],
            data['pm25_env'],
            data['aq_25um']
        ))
    db.commit()
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
    if data['pm25_env'] > 5:
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

    sensor_data = query_db(
        'SELECT max(time) as time, pm25_env, scd_co2 \
           FROM air_quality_log', one = True)
    time_formatted = timezone('UTC').localize(datetime.strptime(sensor_data['time'], '%Y-%m-%d %H:%M:%S')).astimezone(timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    data_formatted = f"{time_formatted} PM 2.5: {sensor_data['pm25_env']} CO2: {sensor_data['scd_co2']}"
    no_override = "checked" if override == 0 else ""
    override_off = "checked" if override == 1 else ""
    override_on = "checked" if override == 2 else ""
    page = f'''Last observation: {data_formatted}<br>
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

@app.route("/scd_co2.png")
def scd_co2():
    return nocache(plot_response("scd_co2"))

@app.route("/scd_temp.png")
def scd_temp():
    return nocache(plot_response("scd_temp"))

@app.route("/scd_hum.png")
def scd_hum():
    return nocache(plot_response("scd_hum"))

@app.route("/bme_temp.png")
def bme_temp():
    return nocache(plot_response("bme_temp"))

@app.route("/bme_gas.png")
def bme_gas():
    return nocache(plot_response("bme_gas"))

@app.route("/bme_hum.png")
def bme_hum():
    return nocache(plot_response("bme_hum"))

@app.route("/bme_pressure.png")
def bme_pressure():
    return nocache(plot_response("bme_pressure"))

@app.route("/pm25_env.png")
def pm25_env():
    return nocache(plot_response("pm25_env"))

@app.route("/aq_25um.png")
def aq_25um():
    return nocache(plot_response("aq_25um"))

def plot_response(metric):
    con = sqlite3.connect("data/data.sqlite")
    data = pd.read_sql_query(f"SELECT time, {metric} FROM air_quality_log WHERE CAST(strftime('%S', time) AS INTEGER) < 5 AND time > datetime('now', '-1 day')", con)
    data['time'] = pd.to_datetime(data['time'], utc=True)

    fig = Figure()
    canvas = backend.FigureCanvas(fig)
    ax = data.plot(x = 'time', y = metric)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(DateFormatter('%H:%M', tz = timezone("America/New_York")))
    img_bytes = BytesIO()
    canvas.print_png(img_bytes)
    img_bytes.seek(0)
    return send_file(img_bytes, mimetype='image/png')

def nocache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response
