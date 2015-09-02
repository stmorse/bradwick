# miscutils.py

import json
import math

###

# converts nodes/links to JSON file
# INPUT: node and link matrices
# OUTPUT: network JSON

def networkToJSON(nodes_dict, adj_mx, json_path):
	# jstr will hold the string we write to the json
	jstr = '{'

	# build jstr for nodes
	jstr += '\"nodes\":['
	for a in nodes_dict:
		jstr += json.dumps(a) + ','
	jstr = jstr.rstrip(',') + '],'

	# add links
	jstr += '\"links\":['
	for i, r in enumerate(adj_mx):
		for j, c in enumerate(r):
			if c == 1:
				jstr += '{\"source\":' + str(i) + ','
				jstr += '\"target\":' + str(j) + '},'
	jstr = jstr.rstrip(',') + ']}'

	# write to file
	f = open(json_path, 'w')
	f.write(jstr)
	f.close()

def strategiesToJSON(connections, agents, json_path):
	cstr = '{\"steps\":['

	# each step is an amalgam of both strategies
	# connections = [ [[], []], ... ]
	for s in connections:
		cstr += '['
		# s[0] is US
		for c in s[0]:
			cstr += '{\"source\":' + str(agents[0]) + ','
			cstr += '\"target\":' + str(c) + ','
			cstr += '\"value\":' + str(9) + '},'
		
		for c2 in s[1]:
			cstr += '{\"source\":' + str(agents[1]) + ','
			cstr += '\"target\":' + str(c2) + ','
			cstr += '\"value\":' + str(9) + '},'
		
		cstr = cstr.rstrip(',') + '],'
	
	cstr = cstr.rstrip(',') + ']}'

	# write to file
	with open(json_path, 'w+') as g:
		g.write(cstr)
		g.close()

###

def connect(mx, a, b):
	mx[a][b] = 1
	mx[b][a] = 1

def disconnect(mx, a, b):
	mx[a][b] = 0
	mx[b][a] = 0

###

def secondMax(numbers):
	# returns second highest from a list
	m, m2 = 0, 0
	if numbers[0] > numbers[1]:
		m, m2 = numbers[0], numbers[1]
	else:
		m, m2 = numbers[1], numbers[0]
	
	for x in numbers[2:]:
		if x>m2:
			if x>m:
				m2, m = m, x
			else:
				m2 = x 

	return m2

###

# normal distribution (pdf, cdf) approximations

def norm_dist(x, mean, stddev):
	var = stddev ** 2
	numer = math.exp(-1 * ((x-mean) ** 2) / (2 * var))
	denom = (2 * math.pi * var) ** .5
	return numer/denom

# f(x, mu, sig) = 1/sig * spdf((x-mu) / sig)
def normal_CDF(x, mean, stddev):
	# ZELEN & SEVERO
	b0 =  0.2316419
	b1 =  0.31938153
	b2 = -0.356563782
	b3 =  1.781477937
	b4 = -1.821255978
	b5 =  1.330274429

	z = (x - mean) / stddev

	t = 1 / (1 + (b0 * z))

	prod = b1*t + b2*(t**2) + b3*(t**3) + b4*(t**4) + b5*(t**5)
	norm = norm_dist(z, 0, 1)

	return 1 - (norm * prod)

# inverse cdf approximations
# from http://www.johndcook.com/blog/python_phi_inverse/

def rational_approximation(t):
	# Abramowitz and Stegun formula 26.2.23.
	# the absolute value of the error should be less than 4.5 e-4.
	c = [2.515517, 0.802853, 0.010328]
	d = [1.432788, 0.189269, 0.001308]
	numerator = (c[2]*t + c[1])*t + c[0]
	denominator = ((d[2]*t + d[1])*t + d[0])*t + 1.0
	return t - numerator / denominator 
 
def normal_CDF_inverse(p, mean, stddev):
	# ensure p in (0, 1)
	assert p > 0.0 and p < 1

	# See article above for explanation of this section.
	if p < 0.5:
		# F^-1(p) = - G^-1(p)
		ra = -rational_approximation( math.sqrt(-2.0*math.log(p)) )
		return (ra * stddev) + mean
	else:
		# F^-1(p) = G^-1(1-p)
		ra = rational_approximation( math.sqrt(-2.0*math.log(1.0-p)) )
		return (ra * stddev) + mean

###

# testing method

if __name__ == "__main__":
	# demo
	print secondMax([40, 35, 35, 20, -5, 3])
	

