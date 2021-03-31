'''
Functions responsible for creating training matrices for machine learning
A key idea is passing functions as arguments to other functions to optimize flexibility
'''

import numpy as np

import storage
import dataPreparation
import fisData

# _____________________________________________________________________
# Arguments for collect f_isValidRace
def isIndividualRace(raceInfo):
	# Determine if the race represented by raceInfo is an individual race

	return raceInfo[5] == fisData.raceTypes.index('Individual')

def isDistanceRace(raceInfo):
	# Determines if the race represented by raceInfo is a distance race

	return fisData.isDistance(raceInfo[5])

# ______________________________________________________________________
# Arguments for getFuncProcessResult f_selectRespone
def getPercentBack(result):
	# Returns the % back in this result

	try:
		return result[1:]
	except TypeError:
		return None # Return none if this result doesn't have a percent back

def getRank(result):
	# Returns the rank in this result

	try:
		return result[0:1]
	except TypeError:
		return [result]

def getRankCategory(result):
	# Categorizes the rank of this result

	rank = getRank(result)[0]
	if rank is None:
		return None
	elif rank <= 3:
		return [0]
	elif rank <= 8:
		return [1]
	elif rank <= 15:
		return [2]
	elif rank <= 30:
		return [3]
	else:
		return [4]

def getFuncIsTop(x):
	# Returns a function which will determine if a result is in the top x places

	def isTop(result):
		# Returns 0 or 1 whethor result is in the top x places

		return [int((not result is None) and getRank(result)[0] <= x)]

	return isTop

# ______________________________________________________________________
# Arguments for getFuncGetFeatures f_selectFromRaceInfo
def getFuncGetAverageBestFisPoints(fisPointIndices):
	# Return a function which will return the average best fis points in raceInfo
	# (list_indices): 0-best 1, 1-best 5, 2-best 15, 3-best 30


	def getFisPoints(raceInfo):
		# Returns a list of the average best fis points in raceInfo
		
		feature = []
		for index in fisPointIndices:
			feature += raceInfo[9][index:index+1]
		return feature

	return getFisPoints

# ______________________________________________________________________
# Arguments for getFuncGetFeatures f_selectFromResult
def getFuncWrapInList(f):
	# Returns a function which will wrap the output of the function f in a list
	# Adds another list dimension to what f normally returns
	# f expects one argument

	def wrapper(argument):
		# Wraps the f(value) in a list
		# If f(value) is None, preserves returns None

		output = f(argument)
		if output is None:
			return None
		return [output]

	return wrapper

# ______________________________________________________________________
# Arguments for getFuncProcessResult f_selectFeatures
def getFuncGetFeatures(f_selectFromRaceInfo, f_selectFromResult):
	# Builds a function which creates a feature from a race
	# f_selectFromRaceInfo: Expects a race info list
	# 	Will return a list of feature(s)
	# f_selectFromResult: Expects a race result
	# 	Will return a list of features(s)

	def getFeature(raceInfo, fisNumber):
		# Builds feature(s) from this training example

		results = storage.readFromJson(raceInfo[1])
		if fisNumber in results:
			features = []
			if f_selectFromRaceInfo:
				value = f_selectFromRaceInfo(raceInfo)
				if value is None:
					return None
				else:
					features += value
			if f_selectFromResult:
				value = f_selectFromResult(results[fisNumber])
				if value is None:
					return None
				else:
					features += value
			return features
		return None
		
	return getFeature

# ______________________________________________________________________
# Arguments for getNextFeatures f_isSimilarRace
def isSameType(racesIndex, currentRI, searchRI):
	# Returns True if the races at currentRI and searchRI are the same type

	return racesIndex[currentRI][5] == racesIndex[searchRI][5]

def isSameTechnique(racesIndex, currentRI, searchRI):
	# Returns True if the races at currentRI and searchRI are the same technique

	return racesIndex[currentRI][6] == racesIndex[searchRI][6]

def isSameTypeAndTechnique(racesIndex, currentRI, searchRI):
	# Returns True if the races at currentRI and searchRI are of the same type and technique

	return isSameType(racesIndex, currentRI, searchRI) and \
		isSameTechnique(racesIndex, currentRI, searchRI)

def isSameDiscipline(racesIndex, currentRI, searchRI):
	# Returns True if the races at currentRI and searchRI are either both sprint or both distance

	return fisData.isDistance(racesIndex[currentRI][5]) == fisData.isDistance(racesIndex[searchRI][5])

# ______________________________________________________________________
# Arguments for getFuncProcessResult f_sdCriteria
def getFuncLinearSdCriteria(b0, b1):
	# returns a function which determines a maximum standard deviation for features based on the average for that feature 'category'

	def criteria(mu):

		return b0 + mu*b1

	return criteria

# _______________________________________________________________________
# Primary functions
def getNextFeatures(racesIndex, currentRI, beginRI, fisNumber, f_isSimilarRace, f_selectFeatures):
	# Search for the next applicable race in racesIndex and add the correct features for this race

	searchLimit = 20
	for i in range(beginRI, len(racesIndex)):
		# Look for recent races which are of the same gender and are similar in a specified way
		if racesIndex[i][7] == racesIndex[currentRI][7] and \
			f_isSimilarRace(racesIndex, currentRI, i):

			features = f_selectFeatures(racesIndex[i], fisNumber)
			if features:
				return i, features
			searchLimit -= 1
			if searchLimit == 0:
				return i, None
	return len(racesIndex) - 1, None

def getFuncProcessResult(f_isValidResult, fList_prevRaceCriteria, prevRaceCounts, f_selectFeatures, fList_sdCriteria, f_selectResponce):
	# Returns a function to process the result

	def processResult(result, racesIndex, currentRI, fisNumber):
		# Returns a training row from a result
		# Returns None if this result doesn't meet the criteria

		if f_isValidResult(result):
			# Check that this result has a valid response
			y = f_selectResponce(result)
			if y is None:
				return None

			# Begin building the features
			features = []
			for i in range(0, len(fList_prevRaceCriteria)):
				categoryFeatures = np.array([])
				beginRI = currentRI + 1
				while True:
					while categoryFeatures.shape[0] < prevRaceCounts[i]:
						endRI, raceFeatures = getNextFeatures(racesIndex, currentRI, beginRI, \
							fisNumber, fList_prevRaceCriteria[i], f_selectFeatures)
						if not raceFeatures:
							return None
						beginRI = endRI + 1
						if categoryFeatures.shape[0] == 0:
							categoryFeatures = np.array([raceFeatures])
						else:
							categoryFeatures = np.concatenate((categoryFeatures, [raceFeatures]), axis=0)

					# Get the standard deviation and mean of each column
					mu = np.mean(categoryFeatures, axis=0)
					# Build a 1D vector of maximum standard deviations
					maxSDs = np.array([])
					for i in range(0, len(fList_sdCriteria)):
						mSD = None
						if fList_sdCriteria[i] is None:
							mSD = np.inf
						else:
							mSD = fList_sdCriteria[i](mu[i])
						maxSDs = np.concatenate((maxSDs, [mSD]))

					std = np.std(categoryFeatures, axis=0)
					fail = std > maxSDs # represents which columns have a std greater than whats tolerated
					
					if np.any(fail):
						test = np.absolute(categoryFeatures - mu)
						test = test[:,np.where(fail)[0]]
						locations = np.argmax(test, axis=0)
						categoryFeatures = np.delete(categoryFeatures, locations, axis=0)
					else:
						# All of the standard deviations are less then the maximum amount
						break

				categoryFeatures = categoryFeatures.flatten().tolist()
				features += categoryFeatures

			# Return training row
			return features + y
		else:
			return None

	return processResult

def collect(f_isValidRace, f_processResult):
	# Build training matrices for machine learning
	# f_isValidRace: function which determines which races to consider

	limit = None
	dataMatrix = []
	racesIndex = storage.readFromJson(dataPreparation.racesIndex_fName)

	# Loop through each race
	for i in range(0, len(racesIndex)):
		if f_isValidRace(racesIndex[i]):
			currentResults = storage.readFromJson(racesIndex[i][1])
			# Loop through the result of each athlete in the race
			for fisNumber in currentResults:
				dataRow = f_processResult(currentResults[fisNumber], racesIndex, i, fisNumber)
				if dataRow:
					dataMatrix.append(dataRow)
					if limit:
						limit -= 1
						if limit == 0:
							return dataMatrix
	return dataMatrix

# ______________________________________________________________________
# Prebuilt schemes to collect data
def collect0():
	# !!! OLD !!!
	# y: top30 -> rank
	# X: rank in last 2 races each in discipline and in type, technique

	processResult = getFuncProcessResult(getFuncIsTop(30), 2, 2, getFuncSelect(getRank), getRank)
	return collect(isDistanceRace, processResult)

def collect1():
	# !!! OLD !!!
	# y: top30 -> top10
	# X: rank in last 2 races each in discipline and in type, technique

	processResult = getFuncProcessResult(getFuncIsTop(30), [isSameDiscipline, isSameTypeTechnique], \
		[2, 2], getFuncSelect(getRank), [lambda mu: 12+.1*mu], getFuncIsTop(10))
	return collect(isDistanceRace, processResult)

def collectIndividualPercentBack():
	# y: % behind winner
	# X: % back in last 5 races each in individual races and individual races of this technique

	selectFeatures = getFuncGetFeatures(None, getPercentBack)
	processResult = getFuncProcessResult(lambda result: True, [isSameType, isSameTypeAndTechnique], \
		[5, 5], selectFeatures, [None], getPercentBack)
	return collect(isIndividualRace, processResult)

def collectIndividualPercentBackWithFisPoints():
	# y: % behind winner
	# X: % back and average of the top 15 Fis points in last 5 races each 
	#	in individual races 
	#	and individual races of same technique

	selectFeatures = getFuncGetFeatures(getFuncGetAverageBestFisPoints([2]), getPercentBack)
	processResult = getFuncProcessResult(lambda result: True, [isSameType, isSameTypeAndTechnique], \
		[5, 5], selectFeatures, [None], getPercentBack)
	return collect(isIndividualRace, processResult)

def collectIndividualPercentBackWithFisPointsWithoutOutliers():
	# y: % behind winner
	# X: % back and average of the top 15 Fis points in last 5 races each 
	#	in individual races 
	#	and individual races of same technique
	# Avoids outliers

	selectFeatures = getFuncGetFeatures(getFuncGetAverageBestFisPoints([2]), getPercentBack)
	processResult = getFuncProcessResult(lambda result: True, [isSameType, isSameTypeAndTechnique], \
		[5, 5], selectFeatures, [getFuncLinearSdCriteria(5, 0), getFuncLinearSdCriteria(.05, .5)], \
		getPercentBack)
	return collect(isIndividualRace, processResult)

def collectAllRankCategory():
	# y: rank
	# X: rank in last 5 races for discipline, type, technique, and typeAndTechnique

	selectFeatures = getFuncGetFeatures(None, getRank)
	processResult = getFuncProcessResult(lambda result: True, [isSameDiscipline, isSameType, isSameTechnique, isSameTypeAndTechnique], \
		[1]*4, selectFeatures, [None], getRankCategory)
	return collect(lambda raceInfo: True, processResult)

def collectDistanceRankCategory():
	# y: rank
	# X: rank in last 5 races for discipline, type, technique, and typeAndTechnique
	# *Only considering distance races

	selectFeatures = getFuncGetFeatures(None, getRank)
	processResult = getFuncProcessResult(lambda result: True, [isSameDiscipline, isSameType, isSameTechnique, isSameTypeAndTechnique], \
		[2, 2, 2, 5], selectFeatures, [None], getRankCategory)
	return collect(isDistanceRace, processResult)
