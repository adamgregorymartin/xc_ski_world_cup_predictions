'''
Functions responsible for processing the data from fis-ski.com formatting it consistantly 
'''

import scrape
import fisData
import storage

# Constants
athletes_fName = './data/athletes.json'

rankingsIndex_fName = './data/rankingsIndex.json'
rankingIdsWorkQueue_fName = './data/rankingIdsWorkQueue.json'

raceIdsWorkQueue_fName = './data/raceIdsWorkQueue.json'
racesIndex_fName = './data/racesIndex.json'

defaultFisPoints = 200

def initAthletes():
	# !!! Should only be run 1 time ever !!!
	# Initializes athletes to an empty dictionary: {}

	storage.storeAsJson({}, athletes_fName)

def isFloat(x):
	try:
		float(x)
	except ValueError:
		return False
	return True

def getRanking(listId):
	# Expects the FIS list id for a points list
	# Returns a dictionary containing the fis points for the top 100 mens and womens sprint and distance points
	# Output: {fisNumber (as String): [distancePoints, sprintPoints], ...}
	# Side Effect! Adds new athletes to the athlete dictionary
	# athletes: {fisNumber: [name, country, gender, yob], ...}
	
	athletes = storage.readFromJson(athletes_fName)
	ranking = {}
	for gender in range(2):
		for discipline in range(2):
			pointsList = fisData.getPointsList(listId, gender, discipline)
			if pointsList:
				for athletePoints in pointsList[1:]:
					fisNumber = athletePoints[1]
					if not fisNumber in ranking:
						# Add points to pointsDict
						distancePoints = float(athletePoints[6]) if isFloat(athletePoints[6]) else defaultFisPoints
						if len(athletePoints) >= 10 and isFloat(athletePoints[9]):
							sprintPoints = float(athletePoints[9])
						else:
							sprintPoints = defaultFisPoints
						ranking[fisNumber] = [distancePoints, sprintPoints]
						if not fisNumber in athletes:
							# Add athlete info to athleteDict
							athletes[fisNumber] = athletePoints[2:6];
							if athletes[fisNumber][2] == 'M':
								athletes[fisNumber][2] = fisData.genders.index('Male')
							else:
								athletes[fisNumber][2] = fisData.genders.index('Female')
	storage.storeAsJson(athletes, athletes_fName)
	return ranking

def getRankingDateRanges():
	# Returns a list of dates ranges for all of the current FIS points lists
	# Output: [[listBeginDate, listEndDate], ...]

	indexTable = scrape.getTables(scrape.getHtml('https://data.fis-ski.com/cross-country/fis-points-lists.html'))[0]
	return [[fisData.getDateAsInt(listInfo[2]), fisData.getDateAsInt(listInfo[3])] for listInfo in indexTable[1:] if len(listInfo) == len(indexTable[0]) and listInfo[1] != '']

def initRankingsIndex(dateAsStr):
	# !!! Should only be run 1 time ever !!!
	# Expects a fis points list id and a date in day-month-year format
	# Initializes pointsDictIndex to this single fictitious list: 
	# pointsDictIndex: [[listId, None, None, listEndDate]]

	rankingsIndex = [[0, None, None, fisData.getDateAsInt(dateAsStr)]]
	storage.storeAsJson(rankingsIndex, rankingsIndex_fName)

def resetRankingIdsWorkQueue():
	# Initializes pointsListIds to an empty list: []

	storage.storeAsJson([], rankingIdsWorkQueue_fName)

def addRankingIdsToWorkQueue(idList):
	# !!! This function must be used correctly, otherwise it will mess things up. !!!
	# Adds ids in idList to rankingIdsWorkQueue
	# Assumes idList is in order of least recent to most recent and does not contain list ids that are already in rankingsIndex
	# rankingIdsWorkQueue: [idForOldestListToAdd, ..., idForMostRecentListToAdd]
	
	rankingIdsWorkQueue = storage.readFromJson(rankingIdsWorkQueue_fName)
	for id in idList:
		rankingIdsWorkQueue.append(id)
	storage.storeAsJson(rankingIdsWorkQueue, rankingIdsWorkQueue_fName)

def updateNewRankings():
	# Stores points dictionary files for all new ids in rankingIdsWorkQueue
	# Adds new entries to the beginning of the pointsDictIndex
	# Resets rankingIdsWorkQueue
	# pointsListIndex is updated to: [[listId, fName, listBeginDate, listEndDate]]

	rankingsIndex = storage.readFromJson(rankingsIndex_fName)
	rankingIdsWorkQueue = storage.readFromJson(rankingIdsWorkQueue_fName)
	newDateRanges = [row for row in getRankingDateRanges() if row[0] > rankingsIndex[0][3]]
	if len(rankingIdsWorkQueue) != len(newDateRanges):
		print(str(len(rankingIdsWorkQueue)) + ' new list ids, but ' + str(len(newDateRanges)) + ' new date ranges -> Update aborted')
		return
	for i in range(0, len(rankingIdsWorkQueue)):
		listId = rankingIdsWorkQueue[i]
		ranking = getRanking(listId)
		if not ranking:
			print('List ' + str(listId) + ' is empty.')
		fName = './data/points/points'+str(listId)+'.json'
		storage.storeAsJson(ranking, fName)
		rankingsIndex.insert(0, [listId, fName, newDateRanges[-(i+1)][0], newDateRanges[-(i+1)][1]])
	storage.storeAsJson(rankingsIndex, rankingsIndex_fName)
	resetRankingIdsWorkQueue()

def storeRace(raceId):
	# Expects the race id for a sprint final or mass or interval start world cup ski race
	# Formats this race into specif format: 
	#   distance: {'Fis Id':[Rank, Percent Back], ...}
	#   sprint final: {'Fis Id':Rank, ...}
	# Stores the results in a .csv file
	# Calculates FisN for N = 1,5,15,30 where FisN = (Sum of best N fis points in race)/N
	# Returns information about the race
	# Output: [Race id, File name, Race category, Date (as datetime), Location, Race Type, Technique, Gender, Distance, [Fis1, Fis5, Fis15, Fis30]]

	[info, results] = fisData.getRaceResults(raceId)

	# Ensure this is a world level individual, mass or sprint final race
	isWorldLevel = (info[0] == fisData.raceCategories.index('Stage World Cup') or info[0] == fisData.raceCategories.index('World Cup') or info[0] == fisData.raceCategories.index('Championship'))
	isIndividual = info[3] == fisData.raceTypes.index('Individual') 
	isMass = info[3] == fisData.raceTypes.index('Mass')
	isSprintFinal = info[3] == fisData.raceTypes.index('Sprint Final')
	if not isWorldLevel:
		print(str(raceId) + ': not a World Cup or Championship (Aborted)')
		return None
	if not (isIndividual or isMass or isSprintFinal):
		print(str(raceId) + ': not a sprint final or an individual or mass start race (Aborted)')
		return None

	# Filter the results data into a standard template
	headers = results[0]
	results = results[1:]
	if 'FIS Code' in headers:
		idIndex = headers.index('FIS Code')
	else:
		print(str(raceId)+': no FIS Code column (Aborted)')
		return None
	rankIndex = headers.index('Rank')
	try:
		timeIndex = headers.index('Time')
		winningTime = fisData.getTimeAsFloat(results[0][timeIndex])
		results = [[row[idIndex], int(row[rankIndex]), (fisData.getTimeAsFloat(row[timeIndex]) - winningTime) / winningTime] for row in results if row[rankIndex] != '']
	except ValueError:
		results = [[row[idIndex], int(row[rankIndex])] for row in results if row[rankIndex] != '']
	
	# Find the average fis points for the top 1, 5, 15, and 30 fis points
	rankingsIndex = storage.readFromJson(rankingsIndex_fName)
	ranking_fName = None
	for rankingHandle in rankingsIndex[:-1]: # The last entry is a fake list
		if rankingHandle[2] <= info[1] and rankingHandle[3] >= info[1]:
			ranking_fName = rankingHandle[1]
			break
	if ranking_fName:
		ranking = storage.readFromJson(ranking_fName)
		def getPoints(id):
			if id in ranking:
				return ranking[id][int(isSprintFinal)]
			else:
				return defaultFisPoints
		fisPoints = sorted([getPoints(row[0]) for row in results])
		averageFisPoints = [sum(fisPoints[0:i])/i for i in [1, 5, 15, 30]]
	else:
		averageFisPoints = [defaultFisPoints] * 4
		print(str(raceid)+': points List not found')
	info.append(averageFisPoints)

	# Create results dictionary
	resultsDict = {}
	for row in results:
		if isSprintFinal:
			resultsDict[row[0]] = row[1]
		else:
			resultsDict[row[0]] = row[1:]

	# There 0 to 1 distances since we avoided skiathlons and relays so we can eliminate the list
	if info[6]: 
		info[6] = info[6][0]
	else:
		info[6] = None

	# Store results and return info
	fName = './data/races/race' + str(raceId) + '.json'
	storage.storeAsJson(resultsDict, fName)
	info.insert(0, raceId)
	info.insert(1, fName)
	return info

def resetRaceIdsWorkQueue():
	# Reset raceIdsWorkQueue to an empty list: []

	storage.storeAsJson([], raceIdsWorkQueue_fName)

def addRaceIdsToWorkQueue(idList):
	# Adds ids in idList to raceIdsWorkQueue
	# raceIdsWorkQueue: [newRace0, newRace1, ...]
	
	raceIdsWorkQueue = storage.readFromJson(raceIdsWorkQueue_fName)
	for id in idList:
		raceIdsWorkQueue.append(id)
	storage.storeAsJson(raceIdsWorkQueue, raceIdsWorkQueue_fName)

def initRacesIndex():
	# !!! Should only be run 1 time ever !!!
	# Initialized racesIndex to an empty list: []

	storage.storeAsJson([], racesIndex_fName)

def updateNewRaces():
	# Stores race results for all ids in raceIdsWorkQueue
	# Adds info for each race to the beginning of racesIndex
	# racesIndex is updated to: [[Race id, File name, Race category, Date (as int), Location, Race Type, Technique, Gender, Distance, [Fis1, Fis5, Fis15, Fis30]], ...]

	raceIdsWorkQueue = storage.readFromJson(raceIdsWorkQueue_fName)
	racesIndex = storage.readFromJson(racesIndex_fName)
	for race in raceIdsWorkQueue:
		info = storeRace(race)
		# Figure out where to insert info in racesIndex to maintain order of most recent first
		if info:
			location = 0 # Initialize to 0 for empty racesIndex case
			isDuplicate = False
			for raceIndex in racesIndex:
				if info[0] == raceIndex[0]: # If this race has already been recorded, put it in the same spot and make note to replace the existing entry
					isDuplicate = True
					break
				if info[3] > raceIndex[3]: # If the race occured after the race at i insert it just before the race at i
					break
				location += 1
			if isDuplicate:
				racesIndex[location] = info
			else:
				racesIndex.insert(location, info)
	storage.storeAsJson(racesIndex, racesIndex_fName)
	resetRaceIdsWorkQueue()

def main():
	# Test Module Functionality

	print('Done :)')

if __name__ == '__main__': # Call main() if this was run from the command line
	main()


'''
Points List Ids:
From 300001 and up incrementing by 1
300009 is the first list with a distance rank, missing 300027 and 300118
300030 is the first list with a sprint rank
Ids skip over 300118 and 300027

range(300009,300027)+range(300028,300118)+range(300119,300130)

Race Ids:
8200, 1440, 14241 do not have a FIS Code column (they are not being used)

1995: [524, 525, 536, 537, 538, 539, 552, 553, 570, 571, 584, 585, 592, 593, 594, 607, 608, 614, 615, 647, 648, 650, 652, 659, 660, 670, 671]

1996: [5240, 5241]+range(716,720)+range(730,733)+[741,742]+range(753,756)+[781,782,795,796,822,843,844,863,864,874,875]+range(881,885)

1997: [5226, 5227]+[927, 928, 955, 956, 959, 960, 965, 966, 990, 991]+range(1014,1018)+[1028, 1029, 1064, 1065, 1069, 1070, 1076, 1078, 1093, 1094, 1100, 1101]

1998: [5228, 5229]+[1163, 1164]+range(1187,1192)+[1590, 1591, 1220, 1221]+range(1228,1233)+[1275, 1276, 1277, 1279, 1281, 1282]+range(1310,1314)+[1317, 1316]

1999: range(5230, 5238)+[1359, 1360]+range(1383,1387)+[1391, 1392, 1415, 1416]+range(1427,1431)+[1493, 1492, 1494, 1495, 1499, 1498, 1506, 1508, 1528, 1527, 1533, 1532, 1537, 1538]

2000: [145, 146]+range(114,118)+[174, 173, 2862, 2863, 2846, 2847, 165, 166, 5, 4, 21, 22, 90, 91, 140, 139, 137, 136, 158, 157, 2859, 2858, 2851, 2850, 92, 93, 2854, 2855, 72, 73, 128, 129]

2001: [2172, 2173, 2176, 2177, 2630, 2629, 2723, 6764, 6765, 2599, 2600, 10936, 10937, 10939, 10938, 2777, 2779, 6758, 6759, 2660, 2659, 2284, 2285, 2455, 2456, 2342, 2343, 2346, 2347, 2348, 2349, 2355, 2790, 2791, 6761, 6760, 2183, 2182, 2435, 2436, 2431, 2432, 2453, 2454]

2002: [2978, 2977, 2979, 2980, 3313, 3314, 3315, 3316, 3317, 3318, 3396, 3395, 3321, 3322, 3484, 3485, 3198, 3196, 3410, 3409, 3325, 3326, 3328, 3327, 2947, 2948, 3523, 3522, 3525, 3524, 3785, 3786, 3533, 3534, 3536, 3537, 2992, 2991, 3118, 3120, 3650, 3649, 3570, 3571, 3574, 3575]

2003: [4353, 4354, 4721, 3837, 4319, 4320, 4325, 4326, 4327, 4328, 4331, 4332, 4726, 4725, 4336, 4335, 4151, 4152, 4118, 4117, 4315, 4316, 4729, 4730, 4337, 4338, 4731, 4732, 4733, 4734, 4742, 4741, 4743, 4744, 4341, 4342, 4344, 4343, 4155, 4156, 3852, 3851, 4748, 4747]

2004: [5622, 5621, 5421, 5420, 5481, 5480, 5859, 5860, 5946, 5945, 6174, 6171, 5835, 5836, 5807, 5808, 5811, 5812, 5514, 5515, 5920, 5919, 5930, 5929, 5931, 5932, 6170, 6168, 5667, 5668, 5669, 5670, 5454, 5455, 5450, 5451, 5528, 5529, 5531, 5530]

2005: [8083, 8082, 7231, 7231, 7232, 7233, 7484, 7482, 7994, 7997, 7907, 7906, 7157, 7158, 7162, 7161, 7556, 7555, 8623, 8622, 7969, 7968, 7972, 7971, 7891, 7890, 7897, 7898, 7902, 7903, 8630, 8628, 7271, 7270, 8319, 8317, 8321, 8320, 8187, 8189, 8199, 8200]

2006: [9444, 9445, 9171, 9172, 9173, 9174, 9793, 9795, 9796, 9797, 9799, 9798, 9124, 9123, 9119, 9120, 9043, 9051, 9063, 9062, 9291, 9292, 9384, 9385, 9631, 9632, 9634, 9633, 10695, 10696, 10700, 10701, 10703, 10704, 10241, 10242, 10245, 10243, 9450, 9451, 9453, 9452, 9628, 9627]

2007: [12438, 12439, 12335, 12336, 12338, 12339, 12819, 12818, 12618, 12617, 11813, 11814, 11829, 11830, 11676, 11674, 11678, 11677, 11680, 11679, 11981, 11980, 11664, 11666, 12417, 12416, 12420, 12421, 11590, 11591, 12712, 12713, 12714, 12715, 12589, 12590, 12595, 12596, 12599, 12600, 12395, 12396, 12398, 12399, 11886, 11887, 11889, 11890, 12534, 12536]

2008: [13580, 13579, 13261, 13262, 13263, 13264, 13198, 13199, 13725, 13724, 13723, 13722, 13892, 13891, 13896, 13895, 14059, 14060, 13334, 13332, 13335, 13336, 14055, 14056, 13866, 13867, 14058, 14057, 13730, 13731, 13735, 13734, 13816, 13817, 13483, 13481, 13287, 13288, 13284, 13283, 13617, 13615, 13618, 13619, 13397, 13396]

2009: [14197, 14196, 14202, 14203, 14204, 14205, 14206, 14207, 14213, 14212, 14463, 14464, 14467, 14468, 14216, 14217, 14228, 14229, 14224, 14225, 14223, 14222, 14231, 14230, 14240, 14241, 14243, 14242, 14246, 14247, 15233, 15234, 15237, 15238, 14259, 14258, 14260, 14261, 14499, 14500, 14505, 14506, 14511, 14512, 14264, 14265, 14266, 14267, 14472, 14471, 14473, 14474, 14272, 14273, 14275, 14274]

2010: [16143, 16142, 16149, 16147, 16151, 16150, 16153, 16155, 16158, 16159, 16163, 16161, 16167, 16165, 16168, 16169, 16170, 16171, 16177, 16175, 16181, 16179, 16184, 16185, 16186, 16187, 16190, 16191, 16195, 16193, 16197, 16257, 16202, 16203, 16205, 16207, 16234, 16235, 16237, 16239, 16246, 16247, 16215, 16213, 16216, 16217, 16221, 16219, 16225, 16223, 16227, 16226]

2011: [17434, 17435, 17443, 17445, 17440, 17441, 17451, 17449, 17454, 17455, 17457, 17459, 17460, 17461, 17506, 17507, 17513, 17511, 17519, 17517, 17522, 17523, 17467, 17465, 17470, 17471, 17586, 17587, 17479, 17477, 17483, 17482, 17487, 17485, 17531, 17533, 17536, 17537, 17542, 17543, 17493, 17491, 17495, 17497, 17498, 17499]

2012: [19171, 19172, 19178, 19176, 19180, 19179, 19152, 19150, 19183, 19184, 19186, 19188, 19193, 19194, 19192, 19190, 19155, 19156, 19162, 19160, 19195, 19196, 19198, 19200, 19203, 19204, 19210, 19208, 19216, 19214, 19218, 19217, 20231, 20232, 19224, 19223, 19227, 19228, 19166, 19168, 19169, 19170, 19236, 19234, 19238, 19240, 19242, 19242, 19244, 19246, 19247, 19248, 19250, 19249]

2013: [20654, 20653, 20738, 20658, 20739, 20740, 20664, 20662, 20665, 20666, 20670, 20668, 20673, 20674, 20680, 20678, 20683, 20684, 20685, 20686, 20694, 20692, 20697, 20698, 20702, 20704, 20710, 20712, 20713, 20714, 20752, 20750, 20757, 20758, 20761, 20762, 20718, 20716, 20719, 20720, 20724, 20722, 20725, 20726, 20730, 20728, 20732, 20731, 20734, 20733]

2014: [22342, 22344, 22345, 22346, 22351, 22352, 22356, 22355, 22360, 22358, 22364, 22362, 22437, 22438, 22439, 22440, 22444, 22442, 22446, 22445, 22449, 22450, 22370, 22368, 22376, 22374, 22378, 22377, 22380, 22379, 22384, 22382, 22488, 22486, 22489, 22490, 22495, 22496, 22388, 22386, 22389, 22390, 22394, 22392, 22395, 22396, 22456, 22458]

2015: [24079, 24081, 24082, 24083, 24085, 24087, 24088, 24089, 24094, 24095, 24099, 24097, 24100, 24101, 24102, 24103, 24104, 24105, 24111, 24109, 24113, 24112, 24116, 24117, 24123, 24125, 24129, 24128, 24133, 24131, 24139, 24137, 24141, 24140, 24159, 24157, 24164, 24165, 24168, 24169, 24145, 24143, 24146, 24147, 24151, 24149, 24152, 24153]

2016: [25747, 25749, 25750, 25751, 25764, 25765, 25761, 25763, 25767, 25769, 25770, 25771, 25773, 25775, 25776, 25777, 25785, 25783, 25780, 25781, 25786, 25787, 25788, 25789, 25797, 25795, 25800, 25801, 25805, 25807, 25808, 25809, 25811, 25813, 25814, 25815, 25817, 25816, 25819, 25821, 25825, 25827, 25828, 25829, 25831, 25833, 25837, 25839, 25843, 25842]

2017: [27660, 27658, 27661, 27662, 27664, 27666, 27667, 27668, 27673, 27674, 27676, 27678, 27679, 27680, 27746, 27744, 27747, 27748, 27753, 27754, 27756, 27755, 27686, 27684, 27690, 27689, 27696, 27694, 27697, 27698, 27702, 27700, 27710, 27708, 27711, 27712, 27730, 27732, 27737, 27738, 27741, 27742, 27716, 27714, 27717, 27718, 29535, 29536, 29538, 29537]

'''