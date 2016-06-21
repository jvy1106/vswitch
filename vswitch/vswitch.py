'''classes to manage various AWS environments'''
import sys
import os
import yaml
import argparse
import time
import boto.ec2
import boto.ec2.elb


def get_config(config_path):
    with open(config_path, 'r') as fd:
        config = yaml.load(fd)

    if 'aws-settings' not in config:
        raise VirtualSwitchConfigError('error: missing aws-settings section')
    elif not config['aws-settings'].get('region'):
        raise VirtualSwitchConfigError('error: aws-settings: region setting')

    if 'environments' not in config:
        raise VirtualSwitchConfigError('error: missing environments section')

    #setup default structure if values are missing in config
    for environment in config['environments'].keys():
        if not config['environments'][environment].get('instances'):
            config['environments'][environment]['instances'] = []
        if not config['environments'][environment].get('loadbalancers'):
            config['environments'][environment]['loadbalancers'] = []

    return config

def get_ec2_connection(config):
    key = config['aws-settings'].get('aws_access_key_id')
    secret = config['aws-settings'].get('aws_secret_access_key')
    region = config['aws-settings'].get('region')
    #will fallback to boto settings if not defined in vswitch config
    return boto.ec2.connect_to_region(region, aws_access_key_id=key, aws_secret_access_key=secret)

def get_elb_connection(config):
    key = config['aws-settings'].get('aws_access_key_id')
    secret = config['aws-settings'].get('aws_secret_access_key')
    region = config['aws-settings'].get('region')
    #will fallback to boto settings if not defined in vswitch config
    return boto.ec2.elb.connect_to_region(region, aws_access_key_id=key, aws_secret_access_key=secret)


class VirtualSwitchConfigError(Exception): pass
class VirtualSwitchInvalidEnvironment(Exception): pass

class VirtualSwitch(object):

    def __init__(self, config_path):
        self._config = get_config(config_path)
        self._ec2 = get_ec2_connection(self._config)
        self._elb = get_elb_connection(self._config)

    def _get_instances(self, environment):
        if environment not in self._config['environments']:
            raise VirtualSwitchInvalidEnvironment('error: unknown environment %s' % environment)

        return self._ec2.get_only_instances(instance_ids=self._config['environments'][environment]['instances'])

    def _get_elbs_and_instance_ids(self, environment):
        if environment not in self._config['environments']:
            raise VirtualSwitchInvalidEnvironment('error: unknown environment %s' % environment)
        
        elbs = self._elb.get_all_load_balancers(load_balancer_names=self._config['environments'][environment]['loadbalancers'].keys())
        return ((lb, self._config['environments'][environment]['loadbalancers'][lb.name]) for lb in elbs)
 
    def get_environments(self):

        return self._config['environments'].keys()

    def get_status(self, environment):
        status = {
            'running': [],
            'pending': [],
            'stopped': [],
            'stopping': [],
            'servers': {},
        }

        for server in self._get_instances(environment):
            info = {}
            info['name'] = server.tags.get('Name', '')
            info['state'] = server.state
            info['state_code'] = server.state_code
            info['dns'] = server.dns_name
            info['ip'] = server.ip_address
            info['instance_type'] = server.instance_type
            status['servers'][server.id] = info
            if server.state in status:
                status[server.state].append(server.id)

        server_count = len(status['servers'])
        if len(status['stopped']) == server_count:
            status['env_state'] = 'stopped'
        elif len(status['pending']) > 0:
            status['env_state'] = 'starting'
        elif len(status['stopping']) > 0:
            status['env_state'] = 'stopping'
        else:
            status['env_state'] = 'running'

        return status

    def turn_on(self, environment):
        for server in self._get_instances(environment):
            server.start()

    def turn_off(self, environment):
        for server in self._get_instances(environment):
            server.stop()

    def register_elb_instances(self, environment):
        for lb, instance_ids in self._get_elbs_and_instance_ids(environment):
            lb.register_instances(instance_ids)

    def deregister_elb_instances(self, environment):
        for lb, instance_ids in self._get_elbs_and_instance_ids(environment):
            lb.deregister_instances(instance_ids)

def main():
    '''Entry point to command line vswitch'''
    ap = argparse.ArgumentParser(description='vswitch lets you turn on/off ec2 environments and check current status')
    ap.add_argument('--list', action='store_true', help='list virtual environments')
    ap.add_argument('--status', type=str, help='list status of servers in given virtual environment')
    ap.add_argument('--start', type=str, help='start all servers in given virtual environment')
    ap.add_argument('--stop', type=str, help='stop all servers in given virtual environment')
    ap.add_argument('--config', type=str, help='path to vswitch conf file. defaults to ~/.vswitch.yml')
    args = ap.parse_args()

    config_path = os.path.join(os.path.expanduser('~'), '.vswitch.yml')
    if args.config:
        config_path = args.config

    vswitch = VirtualSwitch(config_path)

    if args.list:
        #list all available virtual environments
        environments = vswitch.get_environments()
        print 'available environments:'
        for env in environments:
            print ' - %s' % env
        sys.exit(0)

    if args.status:
        status = vswitch.get_status(args.status)
        print 'Instance Id\tName\t\tstatus'
        for id, server in status['servers'].iteritems():
            print '%s\t' % id + '%(name)s\t%(state)s' % (server)
        sys.exit(0)

    if args.start:
        vswitch.turn_on(args.start)
        vswitch.register_elb_instances(args.start)
        #elb sometimes gets in weird state if API service is not up when health check happens
        time.sleep(10)
        vswitch.register_elb_instances(args.start)
        sys.exit(0)

    if args.stop:
        vswitch.turn_off(args.stop)
        vswitch.deregister_elb_instances(args.stop)
        sys.exit(0)
