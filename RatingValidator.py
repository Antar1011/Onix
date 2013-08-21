#!/usr/bin/python
# -*- coding: latin-1 -*-

import gzip
import sys

from common import *

tier = str(sys.argv[1])

binSize = 0.01
if (len(sys.argv) > 2):
	binSize = float(sys.argv[3])

maxRD = 100
if (len(sys.argv) > 3):
	maxRD = float(sys.argv[3])

filename="Raw/"+tier#+".txt"
file = gzip.open(filename,'rb')
raw = file.read()
file.close()

raw=raw.split('][')
for i in range(len(raw)):
	if (i>0):
		raw[i]='['+raw[i]
	if (i<len(raw)-1):
		raw[i]=raw[i]+']'

bins=[]
binCenter=binSize/2
while binCenter < 1.0:
	bins.append([binCenter,0,0])
	binCenter = binCenter+binSize

for line in raw:
	battles = json.loads(line)

	for battle in battles:

		if 'rating' not in battle['p1'].keys() or 'rating' not in battle['p1'].keys() or 'outcome' not in battle['p1'].keys():
			if battle['p1']['rating']['rd'] <= maxRD and battle['p2']['rating']['rd'] <= maxRD:
				probWin = victoryChance(battle['p1']['rating']['r'],battle['p1']['rating']['rd'],battle['p2']['rating']['r'],battle['p2']['rating']['rd'])
				for i in xrange(len(bins)):
					if probWin < bins[i][0]+binSize/2:
						bins[i][1]=bins[i][1]+probWin
						if (battle['p1']['outcome'] == 'win':
							bins[i][2]=bins[i][2]+1
						break

for bin in bins:
	print bin[0],bin[1],bin[2]
	
