# export FLASK_APP=app

# todo:
# better data visualization
# stylesheets (?)
# a standalone "status"/analytics page?
# favicon
# what to do with title page

from flask import Flask
from flask import request
from flask import g
from flask import Response
import sqlite3

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
def hello_world():
    return ""

@app.route("/sensor", methods=['GET', 'POST'])
def sensor():
    if request.method == 'POST':
        if valid_password(request.form['password']):
            sensor_data = dict()
            sensor_data['scd_co2'] = float(request.form['scd_co2'])
            sensor_data['scd_temp'] = float(request.form['scd_temp'])
            sensor_data['scd_hum'] = float(request.form['scd_hum'])
            sensor_data['bme_temp'] = float(request.form['bme_temp'])
            sensor_data['bme_hum'] = float(request.form['bme_hum'])
            sensor_data['bme_pressure'] = float(request.form['bme_pressure'])
            sensor_data['bme_altitude'] = float(request.form['bme_altitude'])
            sensor_data['pm10_std'] = int(request.form['pm10_std'])
            sensor_data['pm25_std'] = int(request.form['pm25_std'])
            sensor_data['pm100_std'] = int(request.form['pm100_std'])
            sensor_data['pm10_env'] = int(request.form['pm10_env'])
            sensor_data['pm25_env'] = int(request.form['pm25_env'])
            sensor_data['pm100_env'] = int(request.form['pm100_env'])
            sensor_data['aq_03um'] = int(request.form['aq_03um'])
            sensor_data['aq_05um'] = int(request.form['aq_05um'])
            sensor_data['aq_10um'] = int(request.form['aq_10um'])
            sensor_data['aq_25um'] = int(request.form['aq_25um'])
            sensor_data['aq_50um'] = int(request.form['aq_50um'])
            sensor_data['aq_100um'] = int(request.form['aq_100um'])
            return log_data(sensor_data)
        else:
            return Response(response = "Wrong password", status = "401")
    return get_relay_state();

def valid_password(password):
    return password == "fuck"

def log_data(data):
    db = get_db()
    db.execute(
        'INSERT INTO air_quality_log (scd_co2, scd_temp, scd_hum, bme_temp, bme_gas, bme_hum, bme_pressure, bme_altitude, pm10_std, pm25_std, pm100_std, pm10_env, pm25_env, pm100_env, aq_03um, aq_05um, aq_10um, aq_25um, aq_50um, aq_100um) \
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (
            data['scd_co2'],
            data['scd_temp'],
            data['scd_hum'],
            data['bme_temp'],
            data['bme_gas'],
            data['bme_hum'],
            data['bme_pressure'],
            data['bme_altitude'],
            data['pm10_std'],
            data['pm25_std'],
            data['pm100_std'],
            data['pm10_env'],
            data['pm25_env'],
            data['pm100_env'],
            data['aq_03um'],
            data['aq_05um'],
            data['aq_10um'],
            data['aq_25um'],
            data['aq_50um'],
            data['aq_100um']
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
    if data['pm25_std'] > 5:
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
        'SELECT max(time) as time, pm25_std, scd_co2 \
           FROM air_quality_log', one = True)
    data_formatted = f"{sensor_data['time']} PM 2.5: {sensor_data['pm25_std']} CO2: {sensor_data['scd_co2']}"
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
