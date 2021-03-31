'''
Functions responsible for training a logistic regression model
'''

import numpy as np

import storage
import trainingData
import machineLearning

def cost(X, y, theta, reg):
	# Expects training matrix (X), column vector of labels (y), 
	# 	column vector of coefficents (theta), and regularization constant (reg)
	# Returns logistic regression cost, gradient

	m = X.shape[0]
	h = machineLearning.sigmoid(X.dot(theta))
	J = np.sum(np.log(h) * (-y) - np.log(1-h) * (1-y)) / m
	J = J + np.sum(theta[1:,:] ** 2) * reg / (2*m) # add regularization
	grad = (np.transpose(X).dot(h-y)) / m
	grad[1:,:] = grad[1:,:] + theta[1:,:] * reg / m # add regularization
	return J, grad

def predictProb(X, theta):
	# predic yHat

	return machineLearning.sigmoid(X.dot(theta))

def predictBool(X, theta):
	# classify yHat to either 0 or 1

	return np.round(predictProb(X, theta), 0)

def accuracy(X, y, theta):
	# return theta's training accuracy

	p = predictBool(X, theta)
	return np.mean((p == y).astype(int))

def trainLogisticRegression(data, order, reg):
	# data is numpy matrix
	# order is the maximum degree of each expansion

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
	theta, costHistory = machineLearning.gradientDescent(X, y, theta, cost, .05, reg, 10000)
	if True:
		print('Progression of cost through gradient descent:')
		print(costHistory[0])
		print(costHistory[int(len(costHistory)/2)])
		print(costHistory[-1])

	# Output
	print('Training Accuracy: ' + str(accuracy(X, y, theta)))
	theta = machineLearning.undoNormalizeTheta(theta, mu, sigma)
	return theta

def trainWithoutOutliers(data, order, reg, sds):
	# Train twice
	# The first time, train like normal
	# Then remove outliers, and train again
	# Theoretically this could improve performance on a test set 

	# Set up
	theta = trainLogisticRegression(data, order, reg)
	X = data[:,:-1]
	X = machineLearning.expandFeatures(X, order)
	y = data[:,-1:]

	error = np.absolute(predictProb(X, theta) - y)
	mu = np.mean(error)
	print('Average abs(error) original: ' + str(mu))
	sd = np.std(error)
	goodRows = np.where(error < (sds*sd + mu))[0]
	print('Removed ' + str(X.shape[0] - goodRows.shape[0]) + ' training samples.')
	newTheta = trainLogisticRegression(data[goodRows,:], order, reg)
	newMu = np.mean(np.absolute(predictProb(X[goodRows,:], newTheta) - y[goodRows,:]))
	print('Average abs(error) after outlier removal: ' + str(newMu))
	return newTheta

def main():
	# Test Module Functionality

	if False:
		data = trainingData.collect1()
		storage.store2DListAsCsv(data, './data/trainingData/trainingData1.csv')
		data = machineLearning.matrix(data)
	else:
		data = storage.read2DListFromCsv('./data/trainingData/trainingData1.csv')
		data = machineLearning.matrix(data)

	print(str(data.shape[0]) + ' x ' + str(data.shape[1]))
	trainWithoutOutliers(data, 2, 0, 2)	

if __name__ == '__main__': # Call main() if this was run from the command line
	main()
