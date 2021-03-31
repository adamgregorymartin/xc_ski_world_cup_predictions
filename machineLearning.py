'''
Utility functions for machine learning
'''

import numpy as np

def matrix(twoDList):
	# Expects a 2 dimension python list
	# Returns a numpy matrix with float64 types

	return np.array(twoDList, dtype=np.float64)

def shuffle(data):
	# Expects numpy matrix
	# Returns the matrix shuffled along the first dimension

	np.random.shuffle(data)
	return data

def partitionData(data, parts):
	# Expects (m)x(n+1) numpy matrix of X and y values (data should not include the bias column)
	# Return TODO

	m = data.shape[0]
	output = []
	begIndex = 0
	for i in range(0, len(parts)):
		endIndex = int(np.sum(parts[0:i+1]) * m)
		output.append(data[begIndex:endIndex,:])
		begIndex = endIndex
	return output

def addBiasCol(X):
	# Preprends a column of 1.0s to the matrix X

	m = X.shape[0]
	return np.concatenate((np.ones((m,1)),X), axis=1)

def normalize(X):
	# Maps all of the features to the same range
	# Each new_feature = (old_feature - col_mean) / (col_sd)

	mu = np.mean(X, axis=0)
	sigma = np.std(X, axis=0)
	Xnorm = (X - mu) / sigma
	return Xnorm, mu, sigma

def undoNormalizeTheta(theta, mu, sigma):
	# Adjusts theta coefficients so they correspond to the pre-normalized x values

	theta[1:,0] = theta[1:,0] / sigma
	theta[0,:] = theta[0,:] - mu.dot(theta[1:,:])
	return theta

def expandFeatures(X, degree):
	# Expects training matrix (X) 
	# 	and the maximum degree of each feature in the expanded training matrix (degree)
	# Returns a complete degree order training matrix

	def recExpandFeatures(X, powers, degree):
		# Recursive instrument
		# Expects a list of the total degree of the following features (powers)

		if len(powers) == X.shape[1]:
			col = np.ones(X.shape[0])
			for i in range(X.shape[1]-1, -1, -1):
				power = powers[i] - np.sum(powers[i+1:])
				powers[i] = power
				col = col * (X[:,i] ** power)
			return np.transpose([col])

		output = np.empty((X.shape[0],0))
		for i in range(0, degree+1):
			partial = recExpandFeatures(X, powers + [i], i)
			output = np.concatenate((output, partial), axis=1)
		return output

	return recExpandFeatures(X, [], degree)

def gradientDescent(X, y, theta, f_cost, alpha, reg, nIterations):
	# Returns [theta, costHistory]
	# theta is adjusted on each iteration by:
		# theta_j = theta_j - alpha * grad_j
		# *Note that all theta coefficients are updated simaltaneously

	costHistory = np.zeros(nIterations)
	for i in range(0, nIterations):
		costHistory[i], grad = f_cost(X, y, theta, reg)
		theta = theta - alpha * grad
	return theta, costHistory

def sigmoid(Z):
	# Expects a matrix Z
	# Returns a matrix of size Z where each element in Z is mapped with the function 
	#	1/(1+e^-z)

	return 1 / (1 + np.exp(-Z))
