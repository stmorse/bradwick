# GameMain.py
# Bradwick rewrite - exhaustive or greedy algorithm
# Separates majority of the sim code into NetworkSimulator.py
# INPUT: network JSON
# OUTPUT: best TB/US strat, sim stats

import itertools
import json
import math
import random
import sys
import time

import miscutils
import NetworkSimulator

###

# read in sys arg as network filename
if (len(sys.argv[1]) > 0):
	network_path = sys.argv[1]
else:
	print "Requires input file of form *.json"
	quit(0)

# load network from file
network = []
with open(network_path, 'rU') as data:
	network = json.load(data)

pop_total = len(network['nodes'])

# US/TB agents
cur_agent = 1 					# index of agent being evaluated
agents = []						# (0 = US, 1 = TB)
agents.append(pop_total - 2)	# node # of US
agents.append(pop_total - 1)	# node # of TB
agent_connects = [ [], [] ]		# US/TB connections

# tracker to build JSON (3D array)
all_connections = []			# each row will have new agent_connects

# game settings (defaults)
lambda_penalty = 0			# [0, 1] penalty for same strategy (0 worst)
payoff_type = 0				# 0=mean belief, 1=nodes won
node_won_thresh = .1		# +/- thresh for node to count as "won"
z = 3 						# number of connections per agent
steps = 5					# number of steps in the game
num_realizations = 10 		# number of sims per candidate strategy
avg_interactions = 30		# (mu) avg int per step
sigma = 1					# (stddev) for interaction amt

# algorithm type settings (defaults)
search_type = 'Greedy'
algo_loops = {'Exhaustive': 1, 'Greedy': z}

# players (US/TB agent inclusive) and links
players = network['nodes']
adj_dict = network['links']

# convert adj_dict into matrix (adj_dict already redundant source/tgt)
adj_mx = [[0 for col in range(pop_total)] for row in range(pop_total)]
for link in adj_dict:
	adj_mx[link['source']][link['target']] = 1

# build list of all F and F+ node #s
cand_connects = [a['Node'] for a in players if a['Type'] == 'Forceful' \
											or a['Type'] == 'Forceful_1']

# build strategy space based on search type: 
# Greedy: all cand_connects, each as list for compatibility
# Exhaustive: (n+z-1 choose z) combinations of cand_connects
strat_space = []
if search_type == 'Greedy':
	strat_space = [[cc] for cc in cand_connects]
elif search_type == 'Exhaustive':
	strat_space = [list(r) for r in \
		itertools.combinations_with_replacement(cand_connects, z)]
else:
	print "Error. Search types: \"Greedy\" or \"Exhaustive\""
	quit(0)

# build peer pressure thresholds for all nodes
thresholds = [0 for x in range(pop_total)]
for i, p in enumerate(players):
	if p['Type'] == 'Regular':
		thresholds[i] = .5
	elif p['Type'] == 'Forceful' or p['Type'] == 'Forceful_1':
		thresholds[i] = .75
	else:
		thresholds[i] = 1

# show initial stats
print ""
print "Steps: %s, Simulations: %s, Interactions (Avg): %s" % \
	(steps, num_realizations, avg_interactions)
print "Key nodes: %s, Max agent connects: %s, Poss. strategies: %s" % \
	(len(cand_connects), z, len(strat_space))
print "Mean belief of network: ", \
	round(sum(p['Belief'] for p in players)/len(players), 4)
print "\nBeliefs: ", 
for p in players:
	print str(round(p['Belief'], 2)),
print ".\n"

start_time = time.clock()

###

# SIMULATIONS

# STEP LOOP
for stepcount in range(steps):
	# determine number of interactions for this step (normal RV)
	num_interactions = int(math.floor(
		miscutils.normal_CDF_inverse(random.random(),
		avg_interactions, sigma)))

	print "Begin step %s." % (stepcount),
	print "Existing connections: US - %s, TB - %s " % \
		(agent_connects[0], agent_connects[1])
	print "Interaction num this step: %s (avg: %s)" % \
		(num_interactions, avg_interactions)
	print " - Assessing strategies for %s ... " % \
		("US" if cur_agent==0 else "TB")

	# remove all existing connections for current agent
	for node in agent_connects[cur_agent]:
		miscutils.disconnect(adj_mx, agents[cur_agent], node)
	agent_connects[cur_agent] = []

	# for exhaustive-selective:
	#		search strat space of all possible combo's once
	# for greedy-selective:
	#		search single nodes sequentially (z times)
	for x in range(algo_loops[search_type]):
		# returns pair of lists:
		# [0] - [best strategy]
		# [1] - [beliefs after best strategy implemented]
		best_option = NetworkSimulator.getBestStrategy(
			players, adj_mx, thresholds,
			cur_agent, agents, agent_connects,
			node_won_thresh, payoff_type, lambda_penalty,
			strat_space, num_realizations, num_interactions)

		if algo_loops > 1: 
			print " - Greedy pick %s of %s" % (x+1, z)
		print " - Best strategy: ", best_option['Strategy']
		print " - Average belief before strategy: ", \
			sum(p['Belief'] for p in players)/len(players)

		# update actual beliefs of all players to best_strat result
		for v, p in enumerate(players):
			p['Belief'] = best_option['Beliefs'][v]
		
		print " - Average belief after strategy: ", \
			sum(p['Belief'] for p in players)/len(players)

		# for agent being evaluated: connect to new best strategy
		agent_connects[cur_agent].extend( best_option['Strategy'] )
		for node in agent_connects[cur_agent]:
			miscutils.connect(adj_mx, agents[cur_agent], node)

	# end algo-type loop

	print " - US connections: ", agent_connects[0]
	print " - TB connections: ", agent_connects[1]

	all_connections.append(agent_connects[:])
	#print all_connections

	# swap agents to evaluate for next step
	cur_agent = 0 if cur_agent==1 else 1

	print "End step ", stepcount

	print "\n Beliefs: ", 
	for p in players:
		print str(round(p['Belief'], 2)),
	print ".\n"

# end step loop

###

end_time = time.clock()

print "TOTAL TIME: %.3f sec" % (end_time-start_time)

# write connections at each step to JSON
c_path = network_path.rstrip(".json") + "_show.json"
miscutils.strategiesToJSON(all_connections, agents, c_path)

print "Complete. Output connections to ", c_path

# end