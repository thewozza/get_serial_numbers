import csv
from netmiko import ConnectHandler
import os
import subprocess

# these are just simple python formatted files with variables in them
from credentials import *

# this loads the devices we're working with from a simple CSV file
# I often alter this file depending on what I'm working on
switches = csv.DictReader(open("switches.csv"))

for row in switches:
	# first we test if the system is pingable - if it isn't we go to the next one
	# this is a very simple error handling mechanism - the script will crash if it can't reach a host
	response = os.system("ping -c 1 -w2 " + row['IP'] + " >/dev/null 2>&1")
	
	if response == 0:
		# this initializes the device object
		# it pulls the username/password/secret variables from a local file called 'credentials.py'
		# the IP is pulled from the 'switches.csv' file
		cisco_switch = {
		    'device_type': 'cisco_ios',
		    'ip': row['IP'],
		    'username': username,
		    'password': password,
		    'port' : 22,          # optional, defaults to 22
		    'secret': secret,     # optional, defaults to ''
		    'verbose': False,       # optional, defaults to False
		}
		
		# this actually logs into the device
		net_connect = ConnectHandler(**cisco_switch)
		
		# the switch inventory has all the information we need but that list is human formatted
		# so there's some extra stuff we have to filter out
		# here we split on the text 'NAM' which is part of "NAME"
		# I wasn't able to split on the newline character and I needed a way
		# to identify the start of a line
		# 
		# the lines look like this:
		# NAME: "Switch 1", DESCR: "WS-C2960-48"
		# PID: WS-C2960-48   , VID: V01  , SN: FDO00000000
		system_inventory = net_connect.send_command('show inventory | i WS-C').split("NAM")
		# this leaves us with an array with elements like this:
		# E: "Switch 1", DESCR: "WS-C2960-48"\nPID: WS-C2960-48   , VID: V01  , SN: FDO00000000
		#
		# this is handy because it is all on one line now
		
		for switch in system_inventory:	# this runs through the inventory output line by line
			switch = switch.split(',')	# split into an array using commas ',' as a delimeter
			if switch[0] == '':	# go to the next line if this one is undefined - this helps skip blank lines
				continue

			# our default position is that the line is garbage
			# if we think we've got a line with our data on it, we'll set this to = 0
			skip = 1
			
			for inventory in switch:	# go through this one line, variable by variable
				if "\n" in inventory:
					# we want everything to the left of the newline
					inventory, dump = inventory.split("\n")
				
				# break up what's left into a k/v pair using a colon as delimeter
				key, value = inventory.split(":")

				if skip == 1:	# if this is true we are at the START of a line
					if key == "E":	# this is where we have NAME: (but NAM got stripped)
						skip = 0	# we've got a good line so we will NOT skip the rest
						# at this point the variable 'key' should look like this:
						# "Switch 1"
						
						# we strip leading/trailing whitespace and apostrophes
						# then split using spaces as a delimiter
						dump, value = value.strip().strip('"').split(' ')
						# now the variable 'value' should contain only the number of the switch
						
						# and we add that to the hostname and IP for our output
						switchOutput = row['Switch'][:-1] + value + "," + row['IP']
						# it should (for now) look like this:
						# SWITCHNAME1,10.10.10.10
					else:	
						# if skip == 1, and we didn't match on "E:" that means this isn't the start
						# of a line, so we can just go the next line altogether
						continue
				else:	
					# if we're here, it means we're NOT Skipping the line
					# and we can cycle through the variables
					
					if "Provisioned" not in value:	# but we only want those switches that are active
						# we're appending additional variables to the output
						# we strip out leading/trailing whitespace and
						# we remove any apostrophes
						switchOutput = switchOutput + "," + value.strip().strip('"')
						# the variable 'switchOutput' should look like this:
						# SWITCHNAME1,10.10.10.10,WS-C2960-48
						# and then
						# SWITCHNAME1,10.10.10.10,WS-C2960-48,V01
						# and then
						# SWITCHNAME1,10.10.10.10,WS-C2960-48,V01,FDO00000000
					else:	
						# if it is just provisioned, it isn't real and there's no serial number to gather
						# so we skip it
						skip = 1
						continue
			# if the variable 'skip' is still true then we can just ignore the rest of this line
			if skip == 1:
				continue
			else:
				# but if it isn't then we're DONE!
				# we can output our actual data here
				print switchOutput
				# and we should get output like this:
				# SWITCH1-SW1,10.10.10.10,WS-C2960-48,V01,FDO00000000
				# SWITCH1-SW2,10.10.10.10,WS-C2960-24,V02,FDO00000011
				#
				# for every reachable switch in our csv file
				
	else:	# this only happens if we can't ping the device
		print row['Switch'] + "," + row['IP'] + ',down'


