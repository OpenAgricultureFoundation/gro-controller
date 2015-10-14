#!/usr/bin/env python3
# Used to take photos for timelapse
# For sequence of 3 photos, use cron as such
"""
0 2 * * * /home/pi/gro-controller/scheduling/preppic.py --purple
1 2 * * * /home/pi/gro-controller/scheduling/takepic.sh purple
2 2 * * * /home/pi/gro-controller/scheduling/preppic.py --white
3 2 * * * /home/pi/gro-controller/scheduling/takepic.sh white
4 2 * * * /home/pi/gro-controller/scheduling/preppic.py --mixed
5 2 * * * /home/pi/gro-controller/scheduling/takepic.sh mixed
"""

import time
import argparse         # allows us to pass in some parameters through command line
import logging		# More convenient logging, easier for debug and the like. import in any file you want to log from
import os
import json
import requests

import sys
if sys.version_info < (3, 3, 0):
    from requests import ConnectionError

# To make pycharm and everyone happy, should refer to modules through package
# from services.server import Server

def commandLineInit():
    """argparse stuff, sets program description and command line args. returns dict of arguments
    :return: dict with all command line args
    """

    # argparse provides cmd line description, --help, and args. try grodaemon.py --help
    program_description = "timelapse_prep: config overrides, specifically lighting, for timelapse image to be taken \n"
    program_epilog = ("Note: If multiple logging flags are set, highest one will be chosen.\n"
                      "Default log level is logging.WARNING. --info is nice too."
                      )
    parser = argparse.ArgumentParser(description=program_description,
                                     epilog=program_epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Flags
    parser.add_argument('-p', '--port', help='serial port to connect to, default /dev/ttyACM0', default='/dev/ttyACM0')
    parser.add_argument('-s', '--server', help='Url of server to connect to. Should have trailing slash', default=None)

    parser.add_argument('-v', '--verbose', action='store_true', help='Print verbose output')   # default False
    parser.add_argument('-i', '--info', action='store_true', help="Output info messages to show what's going on")
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet output, only errors and critical')
    parser.add_argument('-qq', '--qquiet', action='store_true', help='Really quiet output, only critical')
    parser.add_argument('-wh', '--white', action='store_true', help='prep picture for white image')    
    parser.add_argument('-pr', '--purple', action='store_true', help='prep picture for purple image')
    parser.add_argument('-mx', '--mixed', action='store_true', help='prep picture for mixed image')
    args = parser.parse_args()
    args_dict = vars(args)	    # convert all args to a dict for convenience. use ex. args_dict['verbose']

    # Get correct log level
    if args_dict['verbose']:
        log_level = logging.DEBUG
    elif args_dict['info']:
        log_level = logging.INFO
    elif args_dict['quiet']:
        log_level = logging.ERROR
    elif args_dict['qquiet']:
        log_level = logging.CRITICAL
    else:
        log_level = logging.WARNING

    # Set up loggers
    logging_format = logging.Formatter('%(asctime)s :: %(name)-12s :: %(levelname)-8s :: %(message)s')

    logging_file = 'timelapse_prep.log'
    logging.basicConfig(level=logging.DEBUG,        # file logger should always be very verbose.
                        datefmt='%y-%m-%d %H:%M',
                        filename=logging_file,
                        filemode='w')
    logging.getLogger('').handlers[0].setFormatter(logging_format)   # we want to have the same format for both outputs

    console_logger = logging.StreamHandler()
    console_logger.setFormatter(logging_format)
    console_logger.setLevel(level=log_level)
    logging.getLogger('').addHandler(console_logger)

    logging.info('Starting timelapse_prep!')
    logging.debug('Logging to %s', os.path.join(os.getcwd(), logging_file))

    logging.getLogger('requests').setLevel(logging.WARNING)

    logging.debug('Input parameters:')
    for arg in args_dict:
        logging.debug('\t'+str(arg) + '\t' + str(args_dict[arg]))

    return args_dict

def sendRequest(url, data, token):
        data_string = json.dumps(data)
        headers = {'Content-type': 'application/json', 'Authorization':'Token '+token}
        req = requests.post(url, params={"many": True}, data=data_string, headers=headers)
        if req.status_code != 200:
            logging.error('Failed to post %s: Code %d', data_string, req.status_code)
        else:
            logging.debug('Posted %d datapoints, took %f secs', len(data_string), req.elapsed.total_seconds())

# Main Code
if __name__ == "__main__":
    cmdargs_dict = commandLineInit()
    
    # Get Server IP
    f = open(os.path.join('/home/pi/', 'server_ip.txt'), 'r')
    server_ip = f.readline();
    f.close()
    base_url = "http://" + server_ip.strip() + "/" 
    
    # Authorization
    data = { 'username':'plantos', 'password':'plantos' }
    data_string = json.dumps(data)
    headers = {'Content-type': 'application/json'}
    req = requests.post(base_url+"auth/login/", params={"many": True}, data=data_string, headers=headers)
    if req.status_code != 200:
        logging.error('Failed to post %s: Code %d', data_string, req.status_code) 
    else:
        logging.debug('Acquired authentication token!')
    token = req.json()['key']
    #print(token)    

   
    # Send Overrides 
    if cmdargs_dict['white'] is True:
        print('Preparing for white pic')
        sendRequest(base_url+"actuator/2/override/", {'duration':90,'value':1}, token) #white
        sendRequest(base_url+"actuator/1/override/", {'duration':90,'value':0}, token) #purple
    elif cmdargs_dict['purple'] is True:
        print('Preparing for purple pic')
        sendRequest(base_url+"actuator/2/override/", {'duration':90,'value':0}, token) #white
        sendRequest(base_url+"actuator/1/override/", {'duration':90,'value':1}, token) #purple
    elif cmdargs_dict['mixed'] is True:
        print('Preparing for mixed pic')
        sendRequest(base_url+"actuator/2/override/", {'duration':90,'value':1}, token) #white
        sendRequest(base_url+"actuator/1/override/", {'duration':90,'value':1}, token) #purple
