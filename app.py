import os
import time
import requests
import threading
from random import randint

import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import downloader
from downloader import log, err

app = flask.Flask(__name__, static_folder = 'client/')
table: downloader.Turntable = None

limiter = Limiter(get_remote_address, app = app, storage_uri = 'memory://')


def alive_conn() -> None:
    
    addr = 'https://alive-ph-dl.onrender.com'
    
    while 1:
        
        time.sleep(randint(4, 8) * 100)
        
        log('alive', 'Refreshing connection to the alive server...')
        res = requests.get(addr)
        log('alive', f'Connection updated. We are at {res} iterations.')

def initiate():
    '''
    Create the table and run the threads.
    '''
    
    # Create the worker table
    log('init', 'Loading turntable...')
    global table
    table = downloader.Turntable(childs = 3)
    
    # Start the workers
    log('init', 'Loading workers...')
    table.start()
    
    #  Star
    log('init', 'Cleaning output...')
    if os.path.exists('client/output/'):
        
        for file in os.listdir('client/output/'):
            log('init', 'Erasing file', file)
            os.remove('client/output/' + file)
    
    else: log('init', 'Output non existent yet.')
    
    log('init', 'Cleaning done.')
    
    # Start the alive conn
    log('init', 'Loading alive connector...')
    threading.Thread(target = alive_conn).start()
    
    log('init', 'Initialisation phase successfull.')


@app.route('/')
def route_home():
    # Handle serving the main page
    
    # We need to run everything after gunicorn start
    if table is None: initiate()
    
    d = 'not created yet'
    if os.path.exists('client/output/'):
        d = os.listdir('client/output/')
    
    log('route-home', 'Refreshed output directory:', d)
    
    return flask.send_file('client/index.html',
                           mimetype = 'text/html')

@app.route('/download', methods = ['POST'])
@limiter.limit('1/min')
def route_download():
    # Handle listenning for downloads
    
    if table is None: initiate()
    
    try:
        call = table.new(flask.request.args)
        assert call.token, 'table returned tempy token'
        
        log('route-dl', 'Successfully created job', call.token)
        return call.token
    
    except AssertionError as error:
        err('route-dl', 'Token creation assertion:', error)
        return 'error:' + ' '.join(error.args), 400

    except Exception as error:
        err('route-dl', 'Unhandled token creation error:', error)
        return 'error:Unknown erro', 400

@app.route('/status')
@limiter.limit('1/second')
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