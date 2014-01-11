#!/usr/bin/python
# -*- coding: latin-1 -*-

import sys

filename = str(sys.argv[1])

binSize = 0.01
if (len(sys.argv) > 2):
	binSize = float(sys.argv[3])

bins=[]
binCenter=0.5+binSize/2
while binCenter < 1.0:
	bins.append([binCenter,0,0,0])
	binCenter = binCenter+binSize

raw=open(filename).readlines();

for line in raw:
	vals=line.split(',')
	probWin = float(vals[0])
	outcome = float(vals[1])
	for i in xrange(len(bins)):
		if probWin < bins[i][0]+binSize/2:
			bins[i][1]+=1
			bins[i][2]+=probWin
			bins[i][3]+=outcome
			break

for bin in bins:
	print bin[0],bin[1],bin[2],bin[3]
