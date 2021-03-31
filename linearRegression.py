'''
Functions responsible for training a linear regression model
'''

import numpy as np

import storage
import trainingData
import machineLearning

def cost(X, y, theta, reg):
	# Expects training matrix (X), column vector of labels (y), 
	# 	column vector of coefficents (theta), and regularization constant (reg)
	# Returns linear regression cost(theta) = 1/(2m) * SUM((predictedValue - actualValue)^2)
	# 	and gradient(theta)

	m = len(y)
	h = np.dot(X, theta)
	d = h - y
	J = np.sum(d**2) / (2*m) + np.sum(theta[1:]**2) * reg / (2*m) 
	grad = np.dot(np.transpose(X), d) / m
	grad[1:] += theta[1:] * reg / m
	return J, grad

def predict(X, theta):
	# predict yHat from X and theta

	return X.dot(theta)

def accuracy(X, y, theta):
	# return the average absolule value of the training error

	error = np.absolute(predict(X, theta) - y)
	return np.mean(error)

def trainLinearRegression(data, order, reg):
	# data is numpy mxn matrix
	# data should not include the constant column
	# order: the maximum power of each feature combination after polynomial expansion
	# reg: regularization constant

	# Get data
	X = data[:,:-1]
	y = data[:,-1:]

	# Add nonlinear terms
	X = machineLearning.expandFeatures(X, order)

	# Normalize features so that gradient descent works well
	# Don't normalize the constant column, because this has sigma=0
	X[:,1:], mu, sigma = machineLearning.normalize(X[:,1:])

	# Initialize theta and run gradient descent
	theta = np.zeros((X.shape[1], 1))
	theta, costHistory = machineLearning.gradientDescent(X, y, theta, cost, 0.001, reg, 10000)
	if True:
		print('Progression of cost through gradient descent:')
		print(costHistory[0])
		print(costHistory[int(len(costHistory)/2)])
		print(costHistory[-1])

	# Output
	print('Average Training Error: ' + str(accuracy(X, y, theta)))
	theta = machineLearning.undoNormalizeTheta(theta, mu, sigma)
	return theta

def trainWithoutOutliers(data, order, reg, sds):
	# Train twice
	# The first time, train like normal
	# Then remove outliers, and train again
	# Theoretically this could improve performance on a test set 

	# Set up
	theta = trainLinearRegression(data, order, reg)
	X = data[:,:-1]
	X = machineLearning.expandFeatures(X, order)
	y = data[:,-1:]

	error = np.absolute(X.dot(theta) - y)
	mu = np.mean(error)
	sd = np.std(error)
	goodRows = np.where(error <= (sds*sd + mu))[0]
	print('Removed ' + str(X.shape[0] - goodRows.shape[0]) + ' training samples.')
	return trainLinearRegression(data[goodRows,:], order, reg)

def main():
	# Test Module Functionality

	if False:
		data = trainingData.collectIndividualPercentBackWithFisPointsWithoutOutliers()
		storage.store2DListAsCsv(data, './data/trainingData/individualPercentBackWithFisPointsWithoutOutliers.csv')
		print(str(len(data))+' x '+str(len(data[0])))
	else:
		data = machineLearning.matrix(storage.read2DListFromCsv('./data/trainingData/individualPercentBackWithFisPointsWithoutOutliers.csv'))
		print(data.shape)
		theta = trainLinearRegression(data, 3, 0)
	
if __name__ == '__main__': # Call main() if this was run from the command line
	main()
