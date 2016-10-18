import bluetooth._bluetooth as bluez
import time,os,serial,blescan,webbrowser,requests
from threading import Timer
from time import sleep
import RPi.GPIO as GPIO
from threading import Thread
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(27, GPIO.IN, pull_up_down = GPIO.PUD_UP)


class Demo:
	def __init__(self):	
		self.menu_i = 2
		self.picking = False
		self.proc = 0
		#self.ser = serial.Serial('/dev/ttyAMA0',9600, timeout = 1)
		self.client = webbrowser.get('epiphany')
		self.cur_beacons = []
		self.all_beacons = []
		self.cur_macs = []
		self.cur_beacon = 0
		self.default = 0	
	def setup_beacons(self):
		class Beacon:
			def __init__(self,id,mac,name,rssi):
				self.id = id
				self.mac = mac
				self.name = name
				self.rssi = rssi

		beacon1 = Beacon(1,'f1:7c:6f:93:0b:ba','MiniBeacon_00402',0)
		beacon2 = Beacon(2,'c1:30:4a:e0:70:45','MiniBeacon_05871',0)
		beacon3 = Beacon(3,'c4:f1:05:59:ff:25','MiniBeacon_06051',0)
		beacon4 = Beacon(4,'f6:81:44:89:9d:0e','MiniBeacon_06516',0)
		beacon5 = Beacon(5,'d1:28:46:26:99:8c','MiniBeacon_06296',0)
		beacon6 = Beacon(6,'f6:d0:15:f2:99:14','MiniBeacon_05880',0)
		beacon7 = Beacon(7,'fake beacon','None Found',-1000)
		self.all_beacons.append(beacon1)
		self.all_beacons.append(beacon2)
		self.all_beacons.append(beacon3)
		self.all_beacons.append(beacon4)
		self.all_beacons.append(beacon5)
		self.all_beacons.append(beacon6)
		self.all_beacons.append(beacon7)
		self.default = beacon7
		for i in range(0,6):
		#	print(all_beacons[i])
			if(self.all_beacons[i].id <= 3):
				self.cur_beacons.append(self.all_beacons[i])
				self.cur_macs.append(self.all_beacons[i].mac)
	
		self.cur_beacon = beacon7
	
	def run_select(self):
		self.picking = False
		os.system("clear")
		if(self.menu_i == 2):
			self.take_pic()
		elif(self.menu_i == 1):
			self.scan_rfid()
		elif(self.menu_i == 0):
			self.scan_ble()


	def take_pic(self):
		print("Press L to take a Picture")
		self.proc = 1
		while(self.proc == 1):
			if(GPIO.input(22) == False):
				os.system("clear")
				print("Taking Picture...")
				os.system("./raspstill.sh")
				self.return_to_menu()	
				
		
	def scan_rfid(self):
		self.proc = 2
		last_read_tag = 0
		while(self.proc == 2):
			time.sleep(.2)
			if(GPIO.input(22) == False):	
				os.system("pkill epiphany")
				self.return_to_menu()
			else:
				cur_RFID = str(self.ser.readline())
				if(cur_RFID != last_read_tag and cur_RFID != ""):
					last_read_tag = int(cur_RFID)
					os.system("clear")
					print "New Tag:" ,cur_RFID
				else:
					os.system("clear")
					if(last_read_tag == 0):
						print("Last Read Tag: None Read")
					else:
						print "Last Read Tag:" , last_read_tag
						print "R for video"
				if(GPIO.input(27) == False):
					url = " "
					if(last_read_tag == 76):
						url = "http://www.youtube.com/watch_popup?v=JMCLmpUERSg"
					elif(last_read_tag == 84):
						url = "http://www.youtube.com/watch_popup?v=4T_Gs6YOO_8"
					if(url == " "):
						print("no tags have been read")
					else:
						self.client.open(url,new=0)		


	def play_cur_vid(self):
		self.proc = 3
		playing = False
		while(self.proc == 3):
			time.sleep(.2)
			if(GPIO.input(22) == False):	
				os.system("pkill epiphany")
				self.return_to_menu()
			elif(playing == False):
				header = {
					"Content-Type":"application/json",
					"Accept":"application/json",
					"AppKey":"1070406e-9e49-459f-81fc-b027c190576a"
				}
				request_url = "http://52.55.219.115/Thingworx/Things/" + self.cur_beacon.name + "/Properties/Youtube_URL"
				resp = requests.get(request_url,headers=header,verify=False)
				data = resp.json()
				url = data['rows'][0]['Youtube_URL']
				playing = True
				self.client.open(url, new=0)


	
	
	def scan_ble(self):
		sock = bluez.hci_open_dev(0)
		blescan.hci_le_set_scan_parameters(sock)
		blescan.hci_enable_le_scan(sock)
		returnedList = blescan.parse_events(sock, 15)
		cur_scanned_beacons = []
		for beacon in returnedList:
		#	print(beacon)
			beacon_parsed_list = beacon.split(',')
               		beacon_MAC = beacon_parsed_list[0]
               		beacon_RSSI = beacon_parsed_list[5]
			temp_list = []
			if(beacon_MAC in self.cur_macs):
					cur_scanned_beacons.append({"MAC":beacon_MAC,"RSSI":beacon_RSSI})
			
			for beacon in self.cur_beacons:
				for data in cur_scanned_beacons:
					if (data["MAC"] == beacon.mac and data['RSSI'] != 0):
						beacon.rssi = data["RSSI"]
						temp_list.append(beacon)
			if not temp_list:
				self.cur_beaconi= self.default
				return
			min_beacon = self.cur_beacon
			for beacon in temp_list:
				if(int(beacon.rssi) > int(min_beacon.rssi) and int(beacon.rssi) != 0):
					min_beacon = beacon
			self.cur_beacon = min_beacon
			self.update_menu()
					
	def update_ble_status(self, beacon):
		os.system("clear")
		print("Localization:")
		print "Closest Beacon: ", beacon.name

	def return_to_menu(self):
		self.proc = 0
		self.picking = True
		self.update_menu()

	def update_menu(self):
		os.system("clear")
		print "Current Room: ", self.cur_beacon.name
		print("\t 1)Play Current Vid")
		print("\t 2)Run RFID")
		print("\t 3)Take Picture")
demo = Demo()
demo.picking = True
demo.setup_beacons()
demo.update_menu()
while demo.proc == 0:
	if(demo.cur_beacon.id == 7):
		demo.scan_ble()
	else:
		clock_count = 0
		while(clock_count < 150):
			time.sleep(.2)
			if(GPIO.input(22) == False):	
				demo.play_cur_vid()
			if(GPIO.input(23) == False):
				demo.scan_rfid()	
			if(GPIO.input(27) == False):
				demo.take_pic()	
			clock_count += 1
		demo.scan_ble()


demo.scan_ble()	
			
GPIO.cleanup()

