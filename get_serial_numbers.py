import csv
from netmiko import ConnectHandler
import os
import subprocess
from credentials import *

switches = csv.DictReader(open("switches.csv"))

rowdict = {}

for row in switches:
	response = os.system("ping -c 1 -w2 " + row['IP'] + " >/dev/null 2>&1")
	if response == 0:
		cisco_switch = {
		    'device_type': 'cisco_ios',
		    'ip': row['IP'],
		    'username': username,
		    'password': password,
		    'port' : 22,          # optional, defaults to 22
		    'secret': secret,     # optional, defaults to ''
		    'verbose': False,       # optional, defaults to False
		}
		net_connect = ConnectHandler(**cisco_switch)
		#system_version = net_connect.send_command('show version | i System Serial').split('System')
		#system_model = net_connect.send_command('show version | i Model Number').split("\n")
		system_inventory = net_connect.send_command('show inventory | i WS-C').split("NAM")
		#print system_inventory
		for switch in system_inventory:
			switch = switch.split(',')
			if switch[0] == '':
				continue
			skip = 1
			for inventory in switch:
				if "\n" in inventory:
					inventory, dump = inventory.split("\n")
				key, value = inventory.split(":")
				if skip == 1:
					if key == "E":
						skip = 0
						dump, value = value.strip().strip('"').split(' ')
						switchOutput = row['Switch'][:-1] + value + "," + row['IP']
					else:
						continue
				else:
					if "Provisioned" not in value:
						switchOutput = switchOutput + "," + value.strip().strip('"')
					else:
						skip = 1
						continue
			if skip == 1:
				continue
			else:
				print switchOutput
	else:
		print row['Switch'] + "," + row['IP'] + ',down'


