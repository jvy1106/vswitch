'''super basic web server to start/stop and monitor virtual environments'''
import sys
import os
import logging
import web
import time
import argparse
from webpyutils import api
from webpyutils import APIServer
from vswitch import VirtualSwitch

#get project path from current file or venv it setup locally
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__)) + '/../'
if 'VIRTUAL_ENV' in os.environ: PROJECT_PATH = os.path.dirname(os.environ['VIRTUAL_ENV']) + '/'
os.chdir(os.path.join(PROJECT_PATH, 'vswitch'))

#default to users .vswitch.yml
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.vswitch.yml')

def css_state(state):
    '''return css state'''
    ret = 'info'
    if state == 'running':
        ret = 'success'
    elif state == 'stopped':
        ret = 'danger'
    return ret

render = web.template.render(os.path.join(PROJECT_PATH, 'vswitch/templates'), base='layout', globals={'state': css_state})
vswitch = VirtualSwitch(CONFIG_PATH)

class Index(object):
    '''server static page'''
    def GET(self):
        data = {}
        for env in vswitch.get_environments():
            data[env] = vswitch.get_status(env)
        return render.index(data)

class VirtualSwitchAPI(object):
    '''get status of all environments'''
    @api 
    def GET(self):
        '''return info about our environments'''
        ret = {'code': 200, 'data': {}}
        for env in vswitch.get_environments():
            ret['data'][env] = vswitch.get_status(env)
        return ret

    @api
    def POST(self):
        '''toggle on/off for an environment'''
        ret = {'code': 200}
        environment = web.input().get('environment')
        toggle = web.input().get('toggle')
        if toggle in ['true', 'True', 'TRUE']:
            toggle = True
        elif toggle in ['false', 'False', 'FALSE']:
            toggle = False

        if toggle is None:
            ret['code'] = 400
            ret['message'] = 'toggle param is required'
            return ret

        if environment is None:
            ret['code'] = 400
            ret['message'] = 'environment param is required'
            return ret

        if environment not in vswitch.get_environments():
            ret['code'] = 404
            ret['message'] = 'unknown environment: %s' % environment
            return ret

        if toggle is True:
            vswitch.turn_on(environment)
            vswitch.register_elb_instances(environment)
            time.sleep(3)
            vswitch.register_elb_instances(environment)
            ret['data'] = vswitch.get_status(environment)

        elif toggle is False:
            vswitch.turn_off(environment)
            vswitch.deregister_elb_instances(environment)
            ret['data'] = vswitch.get_status(environment)

        else:
            ret['code'] = 400
            ret['message'] = 'toggle param must be bool value'

        return ret

URLS = (
    '/', Index,
    '/v1/vswitch', VirtualSwitchAPI,
)

application = web.application(URLS, globals())

def main():
    '''webserver entry point'''
    ap = argparse.ArgumentParser(description='virtual environment switch - webserver')
    ap.add_argument('--port', type=int, default=8888, help='Change the port the service listens on. Default is 8888')
    ap.add_argument('--ip', type=str, default='0.0.0.0', help='Set IP address to listen on. Default to 0.0.0.0')
    ap.add_argument('--threads', type=int, default=10, help='Number of threads in webserver threadpool. Defaults is 10 threads')
    ap.add_argument('--debug', action='store_true', help='Puts the service into a debug mode to aid development')
    args = ap.parse_args()

    #default settings
    web.config.debug = False
    log_level = logging.INFO

    if args.debug:
        web.config.debug = True
        log_level = logging.DEBUG

    server = APIServer(application, server_name='vswitch', log_path=os.path.join(PROJECT_PATH, 'logs/vswitch.log'), log_level=log_level)
    server.run(ip=args.ip, port=args.port, threads=args.threads)

if __name__ == '__main__':
    main()
