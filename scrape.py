'''
Functions responsible for general scraping of data in html format
'''

import urllib2
import re

reTag = '<[^>]*>'
reRestOfTag = '[^>]*>'
reUntilTag = '[^<]*'
reNotAComment = '(?<!<!--)'
reAllNotGreedy = '[\d\D]*?'

def reCapture(contents):
	return '('+contents+')'

def reGroup(contents):
	return '(?:'+contents+')'

def reCaptureInList(list):
	# Expects a nonzero length list of strings
	# Returns a regular expression which captures any string in the list

	re = list[0]
	for item in list[1:]:
		re += '|'+reGroup(item)
	return reCapture(re)

def getHtml(url):
	# Returns the html at the given url

	response = urllib2.urlopen(url)
	return response.read()

def extractText(html):
	# Returns a string with the screen visible text from an html sample

	reoHtmlTag = re.compile(reTag)
	text = reoHtmlTag.sub('', html) # Remove Html tags
	reoWhiteSpace = re.compile('(?:&nbsp;|&nbsp|\s+)')
	return reoWhiteSpace.sub(' ', text).strip() # Replace instances &nbsp, &nbsp, and any sections of white space with a single space. 

def getElementContent(element, html):
	# Expects an html element name, and some html to parse
	# Returns a list of the content between each pair of html tags
	# Note: This will not recognize nested tags of the same kind.

	reo = re.compile(reNotAComment + '<' + element + reRestOfTag + \
		reCapture(reAllNotGreedy) + reGroup('</' + element + '>'))
	return reo.findall(html)

def getTables(pageHtml):
	# Returns a 3d list: tables
	# tables[0] -> the first table on the page
	# tables[0][0] -> the first row in the first table on the page
	# tables[0][0][0] -> the first cell in the first row in the first table on the page

	'''def getTableContent(pageHtml):
		# Returns a list of all the html inside each <table> element

		reoTable = re.compile(reNotAComment+'<table'+reRestOfTag+reCapture(reAllNotGreedy)+reGroup('</table>'))
		return reoTable.findall(pageHtml)'''

	tables = getElementContent('table', pageHtml)

	def getRowContent(tableHtml):
		# Returns a list of all the html inside each <tr> element

		reoRow = re.compile(reNotAComment+'<tr'+reRestOfTag+reCapture(reAllNotGreedy)+reGroup('</tr>'))
		return reoRow.findall(tableHtml)

	tables = [getRowContent(table) for table in tables]

	def getCellContent(rowHtml):
		# Returns a list of all the html insdie each <td> element

		reoCell = re.compile(reNotAComment+'<'+reGroup('td|th')+reRestOfTag+reCapture(reAllNotGreedy)+reGroup('</'+reGroup('td|th')+'>'))
		return reoCell.findall(rowHtml)

	tables = [[getCellContent(row) for row in table] for table in tables]
	return [[[extractText(data) for data in row] for row in table] for table in tables]

def main():
	# Test Module Functionality

	html = getHtml('https://data.fis-ski.com/cross-country/fis-points-lists.html');
	tables = getTables(html)
	for table in tables:
		for row in table:
			print(row)

if __name__ == '__main__': # Call main() if this was run from the command line
	main()
	