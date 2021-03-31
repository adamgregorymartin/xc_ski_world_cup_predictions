'''
Functions responsible for training a neural network model
'''

import numpy as np

import storage
import trainingData
import machineLearning

def sigmoidGradient(Z):
	# Expects Z as a matrix
	# Returns the derivative of the sigmoid function evaluated at Z

	return machineLearning.sigmoid(Z) * (1 - machineLearning.sigmoid(Z))

def getYMatrix(y, K):
	# Converts a column vector of labels to a matrix
	#	Each column corresponds to one category of labels
	# Assumes y contains values 0,1,...,K-1 

	m = y.shape[0]
	if K == 1:
		Y = y
	else:
		Y = np.zeros((m, K))
		for i in range(0, m):
			Y[i,int(y[i,0])] = 1
	return Y

def cost(X, Y, Theta, reg):
	# Expects training matrix (X)
	#	label matrix (Y), 
	# 	list of coefficient matrices (Theta), 
	#	and regularization constant (reg)
	# Returns neural network cost and gradient

	# Get dimensions
	m = X.shape[0]
	L = len(Theta) + 1 # number of layers
	K = Theta[-1].shape[1] # number of output nodes

	# Forward Propogation
	A = []
	Z = []
	A.append(machineLearning.addBiasCol(X))
	Z.append(None)
	for i in range(1, L):
		Z.append(A[i-1].dot(Theta[i-1]))
		A.append(machineLearning.sigmoid(Z[i]))
		if i != L-1:
			A[i] = machineLearning.addBiasCol(A[i])


	# Get cost
	J = np.sum((-Y) * np.log(A[-1]) - (1-Y) * np.log(1-A[-1])) / m
	# Regularization
	for i in range(0, L-1):
		J += (reg / (2*m)) * np.sum(Theta[i][1:,:]**2)
	
	# Get gradient
	# Backward propagation
	D = []
	D.insert(0, A[-1] - Y)
	for i in range(L-2, 0, -1):
		Di = D[0].dot(Theta[i][1:,:].transpose()) * sigmoidGradient(Z[i])
		D.insert(0, Di)
	D.insert(0, None)

	Grad = []
	for i in range(0, L-1):
		Gradi = A[i].transpose().dot(D[i+1]) / m
		# Regularization
		Gradi[1:,:] = Gradi[1:,:] + (reg/m) * Theta[i][1:,:]
		Grad.append(Gradi)

	return J, Grad

def gradientDescent(X, Y, Theta, alpha, reg, nIterations):
	# Returns [Theta, costHistory]
	# Theta is adjusted on each iteration by:
	# 	Theta[i]_jk = Theta[i]_jk - alpha * grad[i]_jk
	#	*Note that all Theta coefficients are updated simaltaneously

	costHistory = np.zeros(nIterations)
	for i in range(0, nIterations):
		costHistory[i], Grad = cost(X, Y, Theta, reg)
		for i in range(0, len(Theta)):
			Theta[i] = Theta[i] - alpha * Grad[i]
	return Theta, costHistory

def forwardPropagation(X, Theta):
	# predict yHats

	A = machineLearning.addBiasCol(X)
	for i in range(0, len(Theta)):
		Z = A.dot(Theta[i])
		A = machineLearning.sigmoid(Z)
		if i != len(Theta)-1:
			A = machineLearning.addBiasCol(A)
	return A

def predict(X, Theta):
	# classify yHat

	yHat = forwardPropagation(X, Theta)
	if yHat.shape[1] > 1:
		yHat = np.argmax(yHat, axis=1)
		return np.transpose([yHat])
	else:
		return np.round(yHat, 0)

def accuracy(X, y, Theta):
	# Returns percent of training examples Theta predicts correctly

	p = predict(X, Theta)
	return np.average((p == y).astype(int))

def accuracyWithin(X, y, Theta, acceptedError):
	# Returns the percnt of training examples Theta classifys within acceptedError of the correct group
	#	Expects acceptedError as integer
	# Assumes quantitative relationship between groups

	p = predict(X, Theta)
	groupError = np.absolute(p - y)
	nGoodResults = np.where(groupError <= acceptedError)[0].shape[0]
	return float(nGoodResults) / X.shape[0]

def trainNeuralNetwork(data, layers, reg):
	# data is numpy matrix
	# layers is a list of layer sizes
		# layers[0] = number of features (not including bias col)
		# layers[-1] = number of labels

	# Set up X and y
	X = data[:,:-1]
	X, mu, sigma = machineLearning.normalize(X)
	y = data[:,-1:]
	Y = getYMatrix(y, layers[-1])

	# Initialize Theta to random values
	Theta = []
	for i in range(0, len(layers)-1):
		Theta.append(np.random.rand(layers[i]+1, layers[i+1]))

	Theta, costHistory = gradientDescent(X, Y, Theta, .05, reg, 5000)
	if True:
		print(costHistory[0])
		print(costHistory[int(len(costHistory)/2)])
		print(costHistory[-1])

	# Output
	print('Training Accuracy: ' + str(accuracy(X, y, Theta)))
	print('Training Accuracy within 0 categories: ' + str(accuracyWithin(X, y, Theta, 0)))
	print('Training Accuracy withing 1 category: ' + str(accuracyWithin(X, y, Theta, 1)))
	Theta[0] = machineLearning.undoNormalizeTheta(Theta[0], mu, sigma)
	return Theta

def trainWithoutOutliers(data, layers, reg, sds):
	# Train twice
	# The first time, train like normal
	# Then remove outliers, and train again
	# Theoretically this could improve performance on a test set 

	# Set up
	Theta = trainNeuralNetwork(data, layers, reg)
	X = data[:,:-1]
	Y = getYMatrix(data[:,-1:], layers[-1])

	error = np.absolute(forwardPropagation(X, Theta) - Y)
	mu = np.mean(error)
	print('Average abs(error) original: ' + str(mu))
	sd = np.std(error)
	print(sd)
	outlierRows = np.where(error >= (sds*sd + mu))[0]
	outlierRows = np.unique(outlierRows)
	print('Removed ' + str(outlierRows.shape[0]) + ' training samples.')
	goodRows = np.arange(0, X.shape[0])
	goodRows = np.delete(goodRows, outlierRows, axis=0)
	newTheta = trainNeuralNetwork(data[goodRows,:], layers, reg)
	newMu = np.mean(np.absolute(forwardPropagation(X[goodRows,:], newTheta) - Y[goodRows,:]))
	print('Average abs(error) after outlier removal: ' + str(newMu))
	return newTheta

def main():
	# Test Module Functionality

	if False:
		data = trainingData.collectDistanceRankCategory()
		print(str(len(data))+' x '+str(len(data[0])))
		storage.store2DListAsCsv(data, './data/trainingData/distanceRankCategory.csv')
	else:
		data = machineLearning.matrix(storage.read2DListFromCsv('./data/trainingData/distanceRankCategory.csv'))
		print(data.shape)
		n = data.shape[1] - 1
		K = int(np.max(data[:,-1]) + 1)
		Theta = trainNeuralNetwork(data, [n, 10, K], 0)

if __name__ == '__main__': # Call main() if this was run from the command line
	main()
