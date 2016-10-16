#!/usr/bin/env python
import math
from numpy import *
import time 
from time import sleep
import blescan
import sys,os
import bluetooth._bluetooth as bluez
from scipy.optimize import leastsq
dev_id = 0
cur_beacons = [] # find a better way throught thingworx
cur_macs = []
all_beacons = []
set_bound = 0
num_of_beacons = 0
class Beacon:
	def __init__(self,x,y,id,mac,name, values=None):
		self.x = x
		self.y = y
		self.id = id
		self.mac = mac
		self.name = name
		if values is None:
			values = []
		self.values = values
		self.rssi = 0		

try:
        sock = bluez.hci_open_dev(dev_id)
        print "ble thread started"

except:
        print "error accessing bluetooth device..."
        sys.exit(1)

blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)

def get_input():
	global num_of_beacons
	global set_bound
	set_bound = input("How many data points in set?")
	num_of_beacons = input("How many beacons in this test?")



def setup():
	get_input();
	beacon1 = Beacon(0,0,1,'f1:7c:6f:93:0b:ba','MiniBeacon_00402')
	beacon2 = Beacon(0,2,2,'c1:30:4a:e0:70:45','MiniBeacon_05871')
	beacon3 = Beacon(.8,1,3,'c4:f1:05:59:ff:25','MiniBeacon_06051')
	beacon4 = Beacon(0,0,4,'f6:81:44:89:9d:0e','MiniBeacon_06516')
	beacon5 = Beacon(.8,1,5,'d1:28:46:26:99:8c','MiniBeacon_06296')
	beacon6 = Beacon(0,0,6,'f6:d0:15:f2:99:14','MiniBeacon_05880')

	all_beacons.append(beacon1)
	all_beacons.append(beacon2)
	all_beacons.append(beacon3)
	all_beacons.append(beacon4)
	all_beacons.append(beacon3)
	all_beacons.append(beacon4)

		
	for i in range(0,num_of_beacons):
#		print(all_beacons[i])
		if(all_beacons[i].id <= num_of_beacons):
			cur_beacons.append(all_beacons[i])
			cur_macs.append(all_beacons[i].mac)
	

def scan_set_data():
	valid_sets = 0
	while (valid_sets < set_bound):
		returnedList = blescan.parse_events(sock, 15)
		cur_scanned_beacons = []
		for beacon in returnedList:
			beacon_parsed_list = beacon.split(',')
                	beacon_MAC = beacon_parsed_list[0]
                	beacon_RSSI = beacon_parsed_list[5]
			if(beacon_MAC in cur_macs):
				cur_scanned_beacons.append({"MAC":beacon_MAC,"RSSI":beacon_RSSI})
		if(len(cur_scanned_beacons) == num_of_beacons):
			for beacon in cur_beacons:
				for data in cur_scanned_beacons:
					if (data["MAC"] == beacon.mac):
						beacon.values.append(data["RSSI"])	
			print("New Set")
			valid_sets = valid_sets + 1
	proc_data()



def proc_data():
	print("\n Processing Data \n")
	points = []
	
	for beacon in cur_beacons:
		tuned_radius = get_tuned_radius(beacon)
		points.append((beacon.x,beacon.y,tuned_radius))
	
	
	module_location = [0,0]
	plsq = leastsq(residuals, module_location, args=(points))
	print("Module location: ")
	print("X: ", plsq[0][1])
	print("Y: ", plsq[0][0])



#Data0 = beacon.x
#Data1 = beacon.y
#Data2 = beacon.raduis

def residuals(point, data):
        d = sqrt( square(data[0] - point[0]) + square(data[1] - point[1]) ) * square(data[2])
        return d

def get_dis(rssi):
	txPower = -59
	ratio = int(rssi)/txPower;
  	if (ratio < 1.0): 
    		return Math.pow(ratio,10);
  	else:
    		distance =  (0.89976)*math.pow(ratio,7.7095) + 0.111;    
    	return distance

def get_tuned_radius(beacon):
	global set_bound
	aver_rssi = 0
	for v in beacon.values:
		aver_rssi += get_dis(v)
	aver_rssi = (aver_rssi / set_bound)
	return aver_rssi		


setup()
scan_set_data()


