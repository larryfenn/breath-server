# export FLASK_APP=app

# todo:
# 1. set up a sqlite db that can be written to in the sensor() method
#    and can be read from in the data() method (maybe just have it download?)
# 2. implement override page

from flask import Flask
from flask import request
from flask import g
import sqlite3

DATABASE = 'data.db'




app = Flask(__name__)

relay_state = True
override = 0 # 0 - inactive, 1 - force off, 2 - force on
last_data = None

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
    cur = get_db().cursor()
    return "<p>Hello world!</p>"

@app.route("/sensor", methods=['GET', 'POST'])
def sensor():
    error = None
    if request.method == 'POST':
        if valid_password(request.form['password']):
            return log_data(request.form['sensor_data'])
        else:
            error = 'Wrong password'
    return get_relay_state();

def valid_password(password):
    return password == "fuck"

def log_data(data):
    # whenever data is logged two things happen
    # 1. it's saved in the sqlite db
    # 2. we check if conditions merit turning the relay on
    set_relay_state(data)
    return get_relay_state()

def set_relay_state(data):
    # logic here for relay state based on last data
    pass

def get_relay_state():
    state = query_db('select * from state limit 1', one = True)
    override = state['override']
    relay_state = state['relay_state']
    if(override == 0):
        if(relay_state):
            return "on"
        else:
            return "off"
    elif(override == 1):
        return "off"
    else:
        return "on"

@app.route("/data")
def data():
    # sqlite? db locally saved
    return "bla"

@app.route("/control")
def control():
    # webpage that shows a toggle for the circuit state
    # allows someone to 'set' the override value
    # one of three choices
    # force on
    # force off
    # normal

    # also show current state
    # and maybe the last observation set

    # for now just randomly set it
    
    return "bla"
