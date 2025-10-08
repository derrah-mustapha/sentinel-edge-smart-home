import os
import sys
import json
import time
import sqlite3
import hashlib
from pathlib import Path
from threading import Thread, Lock
from collections import deque, defaultdict

from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.mqtt_topics import TOPICS

# Config from env (defaults for local testing)
# Support both local and cloud env var names
MQTT_BROKER = os.environ.get('MQTT_BROKER') or os.environ.get('MQTT_BROKER_HOST') or 'localhost'
MQTT_PORT = int(os.environ.get('MQTT_PORT') or os.environ.get('MQTT_BROKER_PORT') or 1883)
MQTT_USER = os.environ.get('MQTT_USERNAME') or os.environ.get('MQTT_USER') or ''
MQTT_PASS = os.environ.get('MQTT_PASSWORD') or os.environ.get('MQTT_PASS') or ''
MQTT_USE_TLS = str(os.environ.get('MQTT_USE_TLS', 'false')).lower() in ('1', 'true', 'yes')
MQTT_CLIENT_ID_PREFIX = os.environ.get('MQTT_CLIENT_ID_PREFIX', 'dashboard')
# Topics
TOPIC_COMMANDS = TOPICS.COMMANDS
TOPIC_GESTURE_RAW = TOPICS.GESTURE_RAW
TOPIC_VOICE_CMD = TOPICS.VOICE_CMD
PUB_TOPIC = os.environ.get('PUB_TOPIC') or TOPIC_GESTURE_RAW

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
socketio = SocketIO(app, cors_allowed_origins='*')

# Basic auth from env (username/password)
ADMIN_USER = os.environ.get('DASHBOARD_USER', 'admin')
ADMIN_PASS = os.environ.get('DASHBOARD_PASS', 'password')

# Simple in-memory state store (topic -> last payload)
state = {}
topics_set = set()

# In-memory recent message log (capped)
MSG_LOG_MAX = 2000
message_log = deque(maxlen=MSG_LOG_MAX)

# Sensor time-series store: topic -> list of (ts, value)
sensor_store = defaultdict(list)

# Audit log: list of {'user':..., 'action':..., 'ts':...}
audit_log = deque(maxlen=2000)

DB_PATH = os.environ.get('DASHBOARD_DB_PATH', str(Path(__file__).resolve().parent / 'dashboard_data.sqlite3'))
db_lock = Lock()

# Helper functions for authentication
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hash_val):
    """Verify password against hash"""
    return hash_password(password) == hash_val

def register_user(username, password):
    """Register a new user. Returns (success, message)"""
    username = username.strip()
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters"
    
    with db_lock:
        try:
            conn = with_db_connection()
            cur = conn.cursor()
            password_hash = hash_password(password)
            cur.execute(
                "INSERT INTO users(username, password_hash, created_ts) VALUES (?, ?, ?)",
                (username, password_hash, time.time())
            )
            conn.commit()
            conn.close()
            return True, "User registered successfully"
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, str(e)

def verify_user(username, password):
    """Verify user credentials. Returns (success, message)"""
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return False, "Invalid username or password"
        
        if verify_password(password, row[0]):
            return True, "Login successful"
        else:
            return False, "Invalid username or password"


COMMAND_CATALOG = {
    'Door': ['door_open', 'door_close'],
    'Fan': ['fan_on', 'fan_off'],
    'Lights': ['lights_on', 'lights_off', 'lights_dim', 'lights_bright'],
    'Windows': [
        'windows_open_all',
        'windows_close_all',
        'window_open_1',
        'window_close_1',
        'window_open_2',
        'window_close_2',
    ],
    'Modes': ['mode_home', 'mode_away', 'mode_sleep', 'mode_guest'],
    'Safety': ['alert_cancel', 'emergency_activate', 'emergency_cancel', 'status_query'],
}

STATE_TOPICS = [
    TOPICS.FAN_STATE_TOPIC,
    TOPICS.LIGHTS_STATE_TOPIC,
    TOPICS.WINDOWS_STATE_TOPIC,
    TOPICS.DOOR_STATE_TOPIC,
    TOPICS.MODE_STATE_TOPIC,
    TOPICS.GAS_VALVE_STATE_TOPIC,
    TOPICS.WATER_VALVE_STATE_TOPIC,
    TOPICS.SENSOR_GAS_TOPIC,
    TOPICS.SENSOR_WATER_TOPIC,
    TOPICS.SENSOR_FLOOD_TOPIC,
    TOPICS.ALERT_GAS_TOPIC,
    TOPICS.ALERT_FLOOD_TOPIC,
]


def with_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_ts REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mqtt_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL,
                retain INTEGER NOT NULL DEFAULT 0,
                qos INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS state_latest (
                topic TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_ts REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                user_name TEXT NOT NULL,
                action TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS command_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                user_name TEXT NOT NULL,
                token TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_mqtt_messages_ts ON mqtt_messages(ts DESC);
            CREATE INDEX IF NOT EXISTS idx_mqtt_messages_topic ON mqtt_messages(topic);
            CREATE INDEX IF NOT EXISTS idx_audit_events_ts ON audit_events(ts DESC);
            CREATE INDEX IF NOT EXISTS idx_command_events_ts ON command_events(ts DESC);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """
        )
        conn.commit()
        conn.close()
        
        # Create default admin user if no users exist
        with db_lock:
            conn = with_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            conn.close()
            
            if count == 0:
                default_user = os.environ.get('DASHBOARD_USER', 'admin')
                default_pass = os.environ.get('DASHBOARD_PASS', 'password')
                register_user(default_user, default_pass)


def db_insert_message(ts, topic, payload, retain, qos):
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mqtt_messages(ts, topic, payload, retain, qos) VALUES (?, ?, ?, ?, ?)",
            (ts, topic, payload, int(retain), int(qos)),
        )
        cur.execute(
            """
            INSERT INTO state_latest(topic, payload, updated_ts)
            VALUES (?, ?, ?)
            ON CONFLICT(topic) DO UPDATE SET
                payload = excluded.payload,
                updated_ts = excluded.updated_ts
            """,
            (topic, payload, ts),
        )
        conn.commit()
        conn.close()


def db_insert_audit(user_name, action):
    ts = time.time()
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO audit_events(ts, user_name, action) VALUES (?, ?, ?)",
            (ts, user_name or 'anon', action),
        )
        conn.commit()
        conn.close()
    return ts


def db_insert_command(user_name, token, source, status='sent'):
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO command_events(ts, user_name, token, source, status) VALUES (?, ?, ?, ?, ?)",
            (time.time(), user_name or 'anon', token, source, status),
        )
        conn.commit()
        conn.close()


def load_state_from_db():
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT topic, payload FROM state_latest")
        rows = cur.fetchall()
        conn.close()

    for topic, payload in rows:
        state[topic] = payload
        topics_set.add(topic)


def get_logs_from_db(limit=200):
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT ts, topic, payload, retain, qos FROM mqtt_messages ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()

    return [
        {'ts': row[0], 'topic': row[1], 'payload': row[2], 'retain': bool(row[3]), 'qos': row[4]}
        for row in rows
    ]


def get_audit_from_db(limit=200):
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT ts, user_name, action FROM audit_events ORDER BY ts DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()

    return [{'ts': row[0], 'user': row[1], 'action': row[2]} for row in rows]


def get_commands_from_db(limit=200):
    with db_lock:
        conn = with_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ts, user_name, token, source, status
            FROM command_events
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()

    return [
        {'ts': row[0], 'user': row[1], 'token': row[2], 'source': row[3], 'status': row[4]}
        for row in rows
    ]

# MQTT client
mqtt_client = mqtt.Client(client_id=f"{MQTT_CLIENT_ID_PREFIX}_{os.getpid()}")
if MQTT_USER:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
if MQTT_USE_TLS:
    try:
        mqtt_client.tls_set()
    except Exception:
        # best-effort: if system certs unavailable, proceed without explicit CA
        try:
            mqtt_client.tls_set(cert_reqs=0)
        except Exception:
            pass


def on_connect(client, userdata, flags, rc):
    print('[MQTT] Connected rc=', rc)
    # Subscribe to all home topics for full live view
    client.subscribe('home/#')
    # Also ensure we listen to gesture/voice topics explicitly
    client.subscribe(TOPIC_GESTURE_RAW)
    client.subscribe(TOPIC_VOICE_CMD)


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8', errors='replace')
    retain = bool(msg.retain)
    qos = getattr(msg, 'qos', 0)
    import time
    ts = time.time()
    entry = {'topic': topic, 'payload': payload, 'retain': retain, 'qos': qos, 'ts': ts}
    # update state
    state[topic] = payload
    # track topics
    try:
        topics_set.add(topic)
    except NameError:
        pass
    # append to message log
    log_entry = {'ts': ts, 'topic': topic, 'payload': payload, 'retain': retain, 'qos': qos}
    message_log.appendleft(log_entry)
    db_insert_message(ts, topic, payload, retain, qos)
    # store numeric sensor values for small charts (if parseable)
    try:
        v = float(payload)
        sensor_store[topic].append((log_entry['ts'], v))
        # cap series
        if len(sensor_store[topic]) > 2000:
            sensor_store[topic] = sensor_store[topic][-2000:]
    except Exception:
        pass
    # emit to web clients (rich entry)
    socketio.emit('mqtt_message', entry)
    # also emit topic list update
    socketio.emit('topic_list_update', list(topics_set))


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


def mqtt_loop():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    mqtt_client.loop_forever()


init_db()
load_state_from_db()

# Prime in-memory logs and audit from DB for faster first render.
for item in get_logs_from_db(limit=500):
    message_log.append(item)
for item in get_audit_from_db(limit=500):
    audit_log.append(item)

# Start MQTT client in thread
mqtt_thread = Thread(target=mqtt_loop, daemon=True)
mqtt_thread.start()


@app.route('/')
def index():
    # Require simple login
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/visualisation')
def visualisation():
    # Breadboard LED monitor - public access (no login required)
    return render_template('visualisation.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '')
        success, msg = verify_user(user, pw)
        if success:
            session['logged_in'] = True
            session['user'] = user
            return redirect(url_for('index'))
        return render_template('login.html', error=msg)
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pw = request.form.get('password', '')
        pw_confirm = request.form.get('password_confirm', '')
        
        if pw != pw_confirm:
            return render_template('register.html', error='Passwords do not match')
        
        success, msg = register_user(user, pw)
        if success:
            session['logged_in'] = True
            session['user'] = user
            return redirect(url_for('index'))
        return render_template('register.html', error=msg)
    return render_template('register.html')



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/logs')
def api_logs():
    # return recent message log (JSON)
    limit = int(request.args.get('limit', 200))
    items = get_logs_from_db(limit=limit)
    return json.dumps(items)


@app.route('/api/topics')
def api_topics():
    return json.dumps(sorted(list(topics_set)))


@app.route('/api/audit')
def api_audit():
    limit = int(request.args.get('limit', 200))
    return json.dumps(get_audit_from_db(limit=limit))


@app.route('/api/commands')
def api_commands():
    limit = int(request.args.get('limit', 200))
    return json.dumps(get_commands_from_db(limit=limit))


@app.route('/api/state')
def api_state():
    return json.dumps(state)


@app.route('/api/system-config')
def api_system_config():
    return json.dumps(
        {
            'topic_commands': TOPIC_COMMANDS,
            'gesture_topic': TOPIC_GESTURE_RAW,
            'voice_topic': TOPIC_VOICE_CMD,
            'command_catalog': COMMAND_CATALOG,
            'state_topics': STATE_TOPICS,
        }
    )


@app.route('/api/sensor/<path:topic>')
def api_sensor(topic):
    # return series for topic
    series = sensor_store.get(topic, [])
    return json.dumps(series)


@socketio.on('connect')
def handle_connect():
    print('[WS] client connected')
    # send current state to new client
    emit('initial_state', state)
    # send topic list
    try:
        emit('topic_list_update', list(topics_set))
    except Exception:
        emit('topic_list_update', [])


def record_audit(user, action):
    ts = db_insert_audit(user, action)
    audit_log.appendleft({'ts': ts, 'user': user or 'anon', 'action': action})


@socketio.on('publish')
def handle_publish(data):
    """Publish MQTT message. data = {'topic':..., 'payload':...} """
    topic = data.get('topic')
    payload = data.get('payload', '')
    qos = int(data.get('qos', 0))
    retain = bool(data.get('retain', False))
    if topic:
        mqtt_client.publish(topic, payload, qos=qos, retain=retain)
        emit('publish_ok', {'topic': topic, 'payload': payload})
        # audit
        user = session.get('user')
        record_audit(user, f'publish {topic} {payload}')
    else:
        emit('publish_error', {'error': 'missing topic'})


@socketio.on('subscribe')
def handle_subscribe(data):
    topic = data.get('topic')
    if topic:
        mqtt_client.subscribe(topic)
        # audit
        user = session.get('user')
        record_audit(user, f'subscribe {topic}')
        emit('subscribed', {'topic': topic})
    else:
        emit('subscribe_error', {'error': 'missing topic'})


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    topic = data.get('topic')
    if topic:
        mqtt_client.unsubscribe(topic)
        user = session.get('user')
        record_audit(user, f'unsubscribe {topic}')
        emit('unsubscribed', {'topic': topic})
    else:
        emit('unsubscribe_error', {'error': 'missing topic'})


@socketio.on('request_logs')
def handle_request_logs(data):
    limit = int(data.get('limit', 200))
    emit('logs', list(message_log)[:limit])


@socketio.on('replay')
def handle_replay(data):
    # replay a stored message (publish it)
    topic = data.get('topic')
    payload = data.get('payload')
    if topic:
        mqtt_client.publish(topic, payload)
        emit('replay_ok', {'topic': topic, 'payload': payload})
        user = session.get('user')
        record_audit(user, f'replay {topic} {payload}')
    else:
        emit('replay_error', {'error': 'missing topic'})


@socketio.on('simulate_gesture')
def handle_simulate_gesture(data):
    # publish to PUB_TOPIC or gesture topic
    token = data.get('token')
    topic = data.get('topic') or PUB_TOPIC
    if token:
        mqtt_client.publish(topic, token)
        emit('simulate_ok', {'topic': topic, 'token': token})
        user = session.get('user')
        record_audit(user, f'simulate_gesture {token}')
        db_insert_command(user, token, 'gesture_sim', status='sent')
    else:
        emit('simulate_error', {'error': 'missing token'})


@socketio.on('simulate_voice')
def handle_simulate_voice(data):
    token = data.get('token')
    topic = data.get('topic') or TOPIC_VOICE_CMD
    if token:
        mqtt_client.publish(topic, token)
        emit('simulate_ok', {'topic': topic, 'token': token})
        user = session.get('user')
        record_audit(user, f'simulate_voice {token}')
        db_insert_command(user, token, 'voice_sim', status='sent')
    else:
        emit('simulate_error', {'error': 'missing token'})


def wait_for_state(topic, since_ts, timeout=5.0):
    """Wait up to timeout seconds for a message for `topic` with ts>since_ts in message_log."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        # check recent messages
        for m in message_log:
            if m.get('topic') == topic and m.get('ts', 0) > since_ts:
                return m
        time.sleep(0.1)
    return None


@socketio.on('device_action')
def handle_device_action(data):
    """Publish a command and wait for state update. data: {cmd_topic, state_topic, payload}"""
    cmd_topic = data.get('cmd_topic')
    state_topic = data.get('state_topic')
    payload = data.get('payload')
    timeout = float(data.get('timeout', 5))
    if not cmd_topic or payload is None or not state_topic:
        emit('device_action_result', {'ok': False, 'error': 'missing parameters'})
        return
    # record time and publish
    now = time.time()
    mqtt_client.publish(cmd_topic, payload)
    user = session.get('user')
    record_audit(user, f'device_action publish {cmd_topic} {payload}')
    # wait for state change
    result = wait_for_state(state_topic, now, timeout=timeout)
    if result:
        emit('device_action_result', {'ok': True, 'topic': state_topic, 'payload': result.get('payload'), 'ts': result.get('ts')})
    else:
        emit('device_action_result', {'ok': False, 'error': 'timeout waiting for state', 'topic': state_topic})


@socketio.on('execute_token')
def handle_execute_token(data):
    token = str(data.get('token', '')).strip()
    source = str(data.get('source', 'dashboard')).strip() or 'dashboard'
    if not token:
        emit('command_result', {'ok': False, 'error': 'missing token'})
        return

    mqtt_client.publish(TOPIC_COMMANDS, token)
    user = session.get('user')
    record_audit(user, f'execute_token {token}')
    db_insert_command(user, token, source, status='sent')
    emit('command_result', {'ok': True, 'token': token, 'topic': TOPIC_COMMANDS})


if __name__ == '__main__':
    # Use eventlet if available (recommended for SocketIO)
    print('Starting dashboard on http://0.0.0.0:5000, MQTT broker', MQTT_BROKER)
    socketio.run(app, host='0.0.0.0', port=5000)
