#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Example program to receive packets from the radio link
#

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from lib_nrf24 import NRF24
import time
import spidev
ID=None
CE=None



config_file=open('config','r')
config=config_file.readlines()
#config=config.split("\n")
for line in config:
	print(line)
	e=line.split('=')
	if e[0]=='CE':
		CE=int(e[1])
	if e[0]=='ID':
		ID=int(e[1])
if ID is None or CE is None:
	print("Bad Config file")
	print("CE: "),
	print(CE)
	print("ID: "),
	print(ID)

	time.sleep(100)

#Type of messages
TYPE_INIT=	1 #Init, used at start up, will always have a dest of 0, and will be on the 'broadcast pipe'
TYPE_LINK_STATUS=2
#
#
#Connection Status
#-1  down
#0	 unsure
#1   up


msg_count=0
connection_list=[]
class Con():
	
class Connection():
	def __init__(self,address):
		self.ID=address
		self.connections={}
		self.last_contact=time.now()
		self.status=1
#class MyRadio(NRF24):
#	def __init__(self):
#pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
pipes=[[0xe7,0xe7,0xe7,0xe7]]
radio2 = NRF24(GPIO, spidev.SpiDev())
radio2.begin(0, CE)

radio2.setRetries(15,15)

radio2.setPayloadSize(100)
radio2.setChannel(0x60)
radio2.setDataRate(NRF24.BR_2MBPS)
radio2.setPALevel(NRF24.PA_MIN)

radio2.setAutoAck(True)
radio2.enableDynamicPayloads()
#radio2.enableAckPayload()

#self.radio2.openWritingPipe(pipes[0])
radio2.openReadingPipe(1, pipes[0])
radio2.startListening()
#radio2.stopListening()

#radio2.printDetails()

#radio2.startListening()
def Have_Connection(address):
	for c in connection_list:
		if c.ID==address:
			
			return True
	return False
def build_msg(dest,payload,typ):
	#payload can be up to 85 char, format will varry based on type
	global msg_count
	global ID
	msg=[]
	msg.append(dest)
	msg.append(ID)
	for x in range(10):
		msg.append(0)
	msg.append(msg_count)
	msg.append(typ)#type of message
	for c in payload:
		msg.append(ord(c))
	msg.append(len(payload))#maybe will be used for checksum?	

	msg_count=msg_count+1
	if msg_count>255:
		msg_count=0
	print msg
	print("Len of msg: "+str(len(msg)))
	print("Should be : "+str(15+len(payload)))
	return msg
def build_ping():
	global msg_count
	global ID
	msg=[]
	msg.append(0) #dest
	msg.append(ID) #orig
	for x in range(10):
		msg.append(0) #trace
	msg.append(msg_count)
	msg.append(TYPE_INIT)
	msg.append(0)#length of body
	return msg
def process_ping(msg):
	print("Ping Received, Processing....")
	address=msg[1]
	if not Have_Connection(address):
		print("New Station heard...")
		#build connection list
		#send response	
	
def process_link_status(msg):
	print("Processing Link Status")
	#we already checked that it was addressed to us	
	address=msg[1]
	if not Have_Connection(address):
		print("New Connection Started....")
		con=Connection(address)
		#Read and store their connection list
		connection_list.append(con)
		#setup connection

def process_msg(msg):
	print("Received a message")
	global ID
	#|DEST|ORIG|TRACE|MSG#|TYPE|BODY|LEN(BODY)|
	#| 0  | 1  |2-11 | 12 | 13 |Var |  len-1  |		min of 15 bytes
	if len(msg)<15:
		print("MSG is too short")
		return
	if msg[13]==TYPE_INIT:
		#will be addressed for 0,  will respond if we dont already have a connection with ORIG
		#ping received
		process_ping(msg)
	if msg[13]==TYPE_LINK_STATUS and msg[0]==ID:
		#received link status
		process_link_status(msg)  
	#this will receive the message, determine if it is ment for me
	#if it is, log it, pull the payload, and move on
	#if not, call forward(msg)
	print("Processing Message")
def forward(msg):
	#this will be a message that we received, but is not ment for me
	#will need to look up destination and see if we can reach it
	print("Forwarding Message")

def wait_for_ping():
	#this will continue till nothing is recvieved on broadcast pipe for 2 sec, which maybe will be ok
	while True:
		cnt=0
		while not radio2.available([0]):
			time.sleep(.25)
			cnt=cnt+1
			if cnt>8:
				print("nothing heard....")
				return
			continue
		recv_buffer=[]
		radio2.read(recv_buffer,radio2.getDynamicPayloadSize())
		process_msg(recv_buffer)

if ID!= 1:
	#not trunk
	print("Not Trunk, sending ping")
	radio2.stopListening()
	radio2.openWritingPipe(pipes[0])
	radio2.write(build_ping())
	radio2.openReadingPipe(1,pipes[0])
	radio2.startListening()
	wait_for_ping()

while True:
	while not radio2.available([0]):
		#time.sleep(.0001)
		continue
	
	recv_buffer = []
	radio2.read(recv_buffer, radio2.getDynamicPayloadSize())
	process_msg(recv_buffer)
	#if recv_buffer[0]>0:
	#print ("Received:") ,
	#print (recv_buffer)
	#radio2.writeAckPayload(1, recv_buffer, len(recv_buffer))
