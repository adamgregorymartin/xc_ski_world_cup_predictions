'''
Functions responsible for collecting data from the fis-ski.com website
'''

import re
from datetime import date, timedelta

import scrape

raceCategories = ['Stage World Cup', 'World Cup', 'Championship', 'Junior Championship', 'U23 Championship', 'Other']
raceTypes = ['Individual', 'Mass', 'Skiathlon', 'Pursuit', 'Sprint Qualification', 'Sprint Final', 'Team Sprint', 'Relay']
raceTechniques = ['Classic', 'Freestyle', 'Classic/Freestyle']
genders = ['Male', 'Female']
disciplines = ['Distance', 'Sprint']

def isDistance(raceTypeIndex):
	# Expects an index for the raceTypes list
	# Returns whethor or not this index corresponds to a sprint or distance race

	return (raceTypeIndex == raceTypes.index('Individual') or raceTypeIndex == raceTypes.index('Mass') or \
		raceTypeIndex == raceTypes.index('Skiathlon') or raceTypeIndex == raceTypes.index('Pursuit'))

def getDateAsInt(dateAsString):
	# Expects date in dd.mm.yyyy format
	# Returns number of days since 01.01.1900

	reoDelimiter = re.compile('[-\.]+')
	parts = reoDelimiter.split(dateAsString)
	delta = date(int(parts[2]), int(parts[1]), int(parts[0])) - date(1900,1,1)
	return delta.days

def getDateAsStr(dateAsInt):
	# Expects date as number of days since 01.01.1900
	# Returns date in dd.mm.yyyy format

	dt = date(1900,1,1) + timedelta(dateAsInt)
	return str(dt.day)+'.'+str(dt.month)+'.'+str(dt.year)

def getTimeAsFloat(timeAsString):
	# Expects a time in HH:MM:SS:S format
	# Returns this time as a float representing the number of seconds

	parts = timeAsString.split(':')
	time = 0
	for i in range(0, len(parts)):
		time += float(parts[-i-1]) * 60**i
	return time

def getRaceResults(raceId):
	# Expects the FIS race id for a cross country ski race
	# Returns a 2 element list: output
	# output[0] -> Information about the race
	# output[1] -> A 2d List of the results

	pageHtml = scrape.getHtml('https://data.fis-ski.com/dynamic/results.html?sector=CC&raceid=' + str(raceId))

	def getRaceInfo(pageHtml):
		# Returns a list with information about this race
		# [Race category index, Date as datetime, Location: 'City, NAT', Race type index, Technique index, Gender index, Distance: [number1, ...]]
		# Race Category: 'World Cup', 'World Championships', 'Olympics'
		# Race Type: 'Mass', 'Individual', 'Skiathlon', 'Pusuit', 'Sprint Qualifier', 'Sprint Final', 'Team Sprint', 'Relay'
		# Gender: 'Male', 'Female'

		reoHeader = re.compile('OFFICIAL RESULTS'+scrape.reAllNotGreedy+'<a'+scrape.reRestOfTag+scrape.reCapture(scrape.reAllNotGreedy)+'</a>'+scrape.reCapture(scrape.reUntilTag)+'<span'+scrape.reRestOfTag+scrape.reCapture(scrape.reUntilTag)+scrape.reAllNotGreedy+scrape.reGroup('<h4>')+scrape.reCapture(scrape.reUntilTag))
		header = reoHeader.search(pageHtml).group(1, 2, 3, 4) # [City, (Country), day.month.year, details]
		
		info = [''] * 7

		def getCategory(raceHeader):
			# Expects a list with information about the race
			# Returns a specific string for each race category

			reoCategory = re.compile(scrape.reCaptureInList(['Stage World Cup', 'World Cup', 'WC', 'START LIST', 'Junior', 'U23', 'World Ski Championships', 'Olympic Winter Games', 'Overall Standings']))
			category = reoCategory.findall(header[3])
			if 'START LIST' in category or 'Overall Standings' in category:
				return raceCategories.index('Not World Cup')
			else:
				if 'Stage World Cup' in category:
					return raceCategories.index('Stage World Cup')
				elif 'World Cup' in category or 'WC' in category:
					return raceCategories.index('World Cup')
				elif 'Olympic Winter Games' in category:
					return raceCategories.index('Championship')
				elif 'World Ski Championships' in category:
					if 'Junior' in category:
						return raceCategories.index('Junior Championship')
					elif 'U23' in category:
						return raceCategories.index('U23 Championship')
					else:
						return raceCategories.index('Championship')
				else:
					return raceCategories.index('Other')				

		info[0] = getCategory(header)
				
		# Date in MM/DD/YYYY format
		info[1] = getDateAsInt(header[2])
		
		# Location in City, NATION{3}
		info[2] = header[0].strip() + ', ' + header[1].strip()[1:-1]
		
		def getRaceType(raceHeader):
			# Expects a list with information about the race
			# Returns a specific string for each race type

			reoRace = re.compile(scrape.reCaptureInList(['\(M\)','Mst', 'Skiathlon', 'Pursuit', 'SP', 'Qual', 'Final', 'Sprint', 'Team', 'Rel']))
			race = reoRace.findall(raceHeader[3])
			if 'Mst' in race or '(M)' in race:
				return raceTypes.index('Mass')
			elif 'Skiathlon' in race:
				return raceTypes.index('Skiathlon')
			elif 'Pursuit' in race:
				return raceTypes.index('Pursuit')
			elif 'SP' in race:
				if 'Qual' in race:
					return raceTypes.index('Sprint Qualification')
				elif 'Final' in race:
					return raceTypes.index('Sprint Final')
			elif 'Sprint' in race:
				if 'Team' in race:
					return raceTypes.index('Team Sprint')
			elif 'Rel' in race:
				return raceTypes.index('Relay')
			else:
				return raceTypes.index('Individual')

		info[3] = getRaceType(header)

		reoTechnique = re.compile(scrape.reCapture('C|F')+scrape.reGroup('\s|$|/'))
		techniques = reoTechnique.findall(header[3])
		if 'C' in techniques and 'F' in techniques:
			info[4] = raceTechniques.index('Classic/Freestyle')
		elif 'C' in techniques:
			info[4] = raceTechniques.index('Classic')
		else:
			info[4] = raceTechniques.index('Freestyle')
		
		reoGender = re.compile(scrape.reCaptureInList(['Men\'s', 'Ladies\'']))
		gender = reoGender.search(header[3]).group(1)
		if gender == 'Men\'s':
			info[5] = genders.index('Male')
		elif gender == 'Ladies\'':
			info[5] = genders.index('Female')
		
		reoDistance = re.compile(scrape.reCapture('\d+'))
		distance = reoDistance.findall(header[3])
		info[6] = [int(num) for num in distance]
		
		return info

	raceInfo = getRaceInfo(pageHtml)
	results = scrape.getTables(pageHtml)[1]
	results = [row for row in results if len(row) == len(results[0])]
	return [raceInfo, results]

def getPointsList(pointsId, genderIndex, disciplineIndex):
	# Expects the FIS list id for a points list and an index specifying the list gender and discipline
	# Returns a list of the top 100 athletes of specified gender for the specified discipline on the list specified
	# Returns a 2d list: output
	# output[0] = [Rank, Fis Code, Competitor, Nation, Gender, YOB, Distance Pts, Distance Rank, , Sprint Pts, Sprint Rank, ]

	genderStr = genders[0][0]
	if genderIndex == genders.index('Female'):
		genderStr = 'L'
	disciplineStr = disciplines[disciplineIndex][0:2].upper()
	pageHtml = scrape.getHtml('https://data.fis-ski.com/dynamic/fis-points-details.html?sector=CC&listid='+str(pointsId)+'&seasoncode=&lastname=&gender='+genderStr+'&firstname=&nation=&order='+disciplineStr+'&fiscode=&birthyear=&Search=Search&limit=100')
	try:
		points = scrape.getTables(pageHtml)[0]
	except IndexError:
		return None
	return [row for row in points if len(row) == len(points[0])]
