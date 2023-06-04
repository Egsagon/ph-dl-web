import time
import flask
import requests
import threading
import downloader
from random import randint
from flask_limiter import Limiter

app = flask.Flask(__name__, static_folder = 'client/')
table: downloader.Turntable = None

def alive_conn() -> None:
    
    addr = 'https://alive-ph-dl.onrender.com'
    
    while 1:
        
        time.sleep(randint(4, 9) * 1000)
        
        print('[ALIVE] Refreshing conn...')
        res = requests.get(addr)
        print(f'[ALIVE] Done. We are at {res.text} iterations.')

def initiate():
    '''
    Create the table and run the threads.
    '''
    
    # Create the worker table
    global table
    table = downloader.Turntable(childs = 5)
    table.start()
    
    # Start the alive conn
    threading.Thread(target = alive_conn).start()

@app.route('/')
def route_home():
    # Handle serving the main page
    
    # We need to run that after gunicorn has started
    # for some reason
    if table is None: initiate()
    
    return flask.send_file('client/index.html',
                           mimetype = 'text/html')

@app.route('/download', methods = ['POST'])
def route_download():
    # Handle listenning for downloads
    
    if table is None: initiate()
    
    try:
        call = table.new(flask.request.args)
        assert call.token, 'failed token invocation'
        return call.token
    
    except AssertionError as err:
        print('Assertion', err)
        return  'error:' + ' '.join(err.args), 400

    except Exception as err:
        print('Unhandled error:', err)
        return 'error:Unknown erro', 400

@app.route('/status')
def route_status():
    # Handle giving the current status of a download
    
    token = flask.request.args.get('token', '')
    if not token: return 'invalid token', 400
    
    for call in table.tracked:
        if call.token == token:
            return flask.jsonify(call.to_dict())
    
    return 'token not found', 400


if __name__ == '__main__':
    
    # Run the app
    app.run(debug = True)

# EOF