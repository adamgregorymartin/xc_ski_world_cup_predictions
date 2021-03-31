'''
Functions responsible for storing and recovering data
'''

import json
import csv

def storeAsJson(anObject, fName):
	# Store object in json file
	# Note: Dictionaries converted to javascript objects
	# Datetime objects not supported

	with open(fName, 'wb') as outFile:
		json.dump(anObject, outFile)

def readFromJson(fName):
	# Reads object from .json file

	with open(fName, 'rb') as inFile:
		return json.load(inFile)

def store2DListAsCsv(a2DList, fName):
	# Stores a 2D python list as a .csv file

	with open(fName, 'wb') as outFile:
		writer = csv.writer(outFile)
		writer.writerows(a2DList)

def read2DListFromCsv(fName):
	# Reads a 2d List from a .csv file

	with open(fName, 'rb') as inFile:
		reader = csv.reader(inFile)
		return [row for row in reader]
