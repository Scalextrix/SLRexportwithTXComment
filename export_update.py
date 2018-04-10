#!/usr/bin/env python

"""export_updater.py takes the transactrions exported from the solarcoin wallet as a .csv and creates another version with the tx-comment appended to each transaction """

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2018, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"


import csv
import getpass
import json
import os.path
import requests
import time

def instruct_wallet(method, params):
        url = "http://127.0.0.1:18181/"
        payload = json.dumps({"method": method, "params": params})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        try:
                response = requests.request("POST", url, data=payload, headers=headers, auth=(rpc_user, rpc_pass))
                return json.loads(response.text)
        except requests.exceptions.RequestException as e:
                print e 
                print 'Backing off for 10 seconds'
                time.sleep(10)
        return instruct_wallet(method, params)

# find solarcoin.conf
if os.name == 'nt':
        user_account = getpass.getuser()
        conf_location = 'C:\Users\{}\AppData\Roaming\SolarCoin\SolarCoin.conf'.format(user_account)
elif os.name == 'posix':
        homedir = os.environ['HOME']
        conf_location = '{}/.solarcoin/solarcoin.conf'.format(homedir)
else:
        conf_location = ''
while True:
        try:
                solarcoin_conf = open(conf_location, 'rb')
                break
        except:
                print('solarcoin.conf not found')
                conf_location = raw_input('Please enter the FULL path to solarcoin.conf: ')

# try to find rpc credentials from solarcoin.conf
rpc_user = ''
rpc_pass = ''
for line in solarcoin_conf:
        line = line.rstrip()
        if line[0:7] == 'rpcuser':
                rpc_user = line[line.find('=')+1:]
        if line[0:11] == 'rpcpassword':
                rpc_pass = line[line.find('=')+1:]
solarcoin_conf.close()
if rpc_user == '' or rpc_pass == '':
        print 'solarcoin.conf found but "rpcuser=" or "rpcpassword=" missing'
        print 'Please add rpcuser=<username_here> and rpcpassword=<password_here> to solarcoin.conf'
        print 'Exit in 10 seconds'
        time.sleep(10)
        sys.exit()

# ask user where the transaction export .csv is located
export_location = raw_input ("Please enter the path and name of the file exported from SolarCoin wallet: ")
while True:
        try:
                export_file = open(export_location, 'rb')
                break
        except:
                print 'Export file not found'
                export_location = raw_input('Please enter the FULL path to the export file (including the filename): ')

# read the export.csv as a list
reader = csv.reader(export_file)
transaction_details = list(reader)
export_file.close()

# extract the transaction hash, ask wallet for transaction detials, append the tx-comment in the list
max_lines = len(transaction_details)
print 'Updating {} rows in {}'.format(max_lines, export_location)
counter = 0
while True:
        tx_confirmed = transaction_details[counter][0]
        tx_hash = transaction_details[counter][6]
        if tx_hash == 'ID' or tx_confirmed == 'false':
                print 'skipping row, either: title, unconfirmed or orphaned'
                counter = counter+1
        else:
                tx_hash = transaction_details[counter][6][0:-4]
                tx_json = instruct_wallet('getrawtransaction', [tx_hash, 1])['result']
                tx_message = str(tx_json['tx-comment'])
                transaction_details[counter].append(tx_message)
                print transaction_details[counter]
                counter = counter+1
        if counter == max_lines:
                break

# write a new .csv with the updated list
newfile = export_location[0:-4]+'_updated.csv'
with open(newfile, "wb") as f:
    writer = csv.writer(f, delimiter=',', lineterminator='\n')
    writer.writerows(transaction_details)
f.close()
