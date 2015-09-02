# NetworkSimulator.py
# Runs exhaustive simulations on given network, returns best strategy
# INPUTS: node beliefs, links, strategy space to search, stubborn agents
# OUTPUT: dict with - best strategy, and updated beliefs per node
# (Returns adj_mx, agent_connects to original state)

import random
import miscutils

# interaction probabilities (1 - alpha[i][j] - beta[i][j] = gamma)
alpha_mx = [ [0, 0, 0, 0],
			 [1, 0, 0, 0],
			 [1,.4, 0, 0],
			 [1, 1, 1, 0] ]
beta_mx =  [ [1, 0, 0, 0],
			 [0,.1,.1, 0],
			 [0,.1,.1, 0],
			 [0, 0, 0, 0] ]

# indices to standardize reference to alpha/beta_mx
ab_indices = { 'Regular': 0, 'Forceful': 1, 
			   'Forceful_1': 2, 'Forceful_2': 3 }

###

def getBestStrategy(players, adj_mx, thresholds,
					cur_agent, agents, agent_connects,
					node_won_thresh, payoff_type, lambda_penalty,
					strat_space, num_realizations, num_interactions):
	# final return dict
	best_option = {'Strategy':[], 'Beliefs':[]}
	
	# list we are searching for, set to empty
	best_strat = []

	# baseline payoff vals (worst than worse case, +/-1 per node)
	best_sum_beliefs = [-len(players) for x in range(len(players))] if cur_agent==0 \
		else [len(players) for x in range(len(players))]

	# STRATEGY SPACE LOOP
	for ss in strat_space:
		# initialize/reset measure variables:

		# fresh copy actual belief state into test_beliefs
		test_beliefs = [p['Belief'] for p in players]

		# holds the average belief for each player over current strategy
		# running sum until all sims are complete
		strat_sum_beliefs = [0 for x in range(len(test_beliefs))]

		# holds the total nodes won US (0) and TB (1) over current strategy
		strat_sum_nodes_won = [0, 0]

		# set new connections for cur_agent 
		agent_connects[cur_agent].extend(ss)
		for c in ss:
			miscutils.connect(adj_mx, agents[cur_agent], c)

		# set alpha penalization if both agents target same node
		penalty = []
		for node in agent_connects[cur_agent]:
			if node in agent_connects[1 if cur_agent==0 else 0]:
				penalty.append(node)

		# REALIZATION LOOP
		for k in range(num_realizations):
			
			# INTERACTIONS LOOP
			for n in range(num_interactions):
				# select our pairwise interaction at random
				# and identify their neighbors (could include US/TB)
				person_i = random.randint(0, len(players) - 1)
				neighbors_i = [j for j, c in enumerate(adj_mx[person_i]) if c == 1]

				# if person_i is US/TB on first turn w/ no neighbors
				if len(neighbors_i) == 0:
					continue

				person_j = neighbors_i[random.randint(0, len(neighbors_i) - 1)]
				neighbors_j = [i for i, r in enumerate(map(list, zip(*adj_mx))[person_j]) if r == 1]

				# identical beliefs will produce no action, skip
				if test_beliefs[person_i] == test_beliefs[person_j]:
					continue
				
				# number of neighbors (excluding each other)
				num_conn_i = len(neighbors_i) - 1
				num_conn_j = len(neighbors_j) - 1

				# in the event we're examining a US/TB connection, z = 1
				# and the US/TB agent only has the one connection
				if (person_i in agents) and num_conn_i == 0:
					num_conn_i += 1
				elif (person_j in agents) and num_conn_j == 0:
					num_conn_j += 1

				# count belief stats for i, j neighbors, exclude each other
				# use test_beliefs since we want to include any in-sim changes
				count_above_i, count_below_i = 0.0, 0.0
				for cand in neighbors_i:
					if cand != person_j:
						if test_beliefs[cand] > test_beliefs[person_i]:
							count_above_i += 1
						elif test_beliefs[cand] < test_beliefs[person_i]:
							count_below_i += 1

				count_above_j, count_below_j = 0.0, 0.0
				sum_above_j, sum_below_j = 0.0, 0.0
				avg_above_j, avg_below_j = 0, 0
				for cand2 in neighbors_j:
					if cand2 != person_i:
						if test_beliefs[cand2] > test_beliefs[person_j]:
							count_above_j += 1
							sum_above_j += test_beliefs[cand2]
						elif test_beliefs[cand2] < test_beliefs[person_j]:
							count_below_j += 1
							sum_below_j += test_beliefs[cand2]
				avg_above_j = sum_above_j / num_conn_j
				avg_below_j = sum_below_j / num_conn_j

				# ALPHA/BETA/GAMMA INTERACTIONS
				
				abx_i = ab_indices[players[person_i]['Type']]
				abx_j = ab_indices[players[person_j]['Type']]
				alpha_ij = alpha_mx[abx_i][abx_j]
				beta_ij = beta_mx[abx_i][abx_j]

				if (person_i in agents):
					if person_j in penalty:
						beta_ij = lambda_penalty
				
				rand1 = random.random()
				rand2 = random.random()

				# BETA interaction (averaging)
				if rand1 <= beta_ij:

					ij_avg_belief = (test_beliefs[person_i] + test_beliefs[person_j]) / 2
				
					# x regresses to mean if y pulls
					# AND ratio of neighbors that direction > y's threshold
					avg_i = False
					avg_j = False
					if test_beliefs[person_i] > test_beliefs[person_j]:
						# test if i will drop
						if (count_below_i / num_conn_i) >= thresholds[person_i]:
							avg_i = True
						# test if j will rise
						if (count_above_j / num_conn_j) >= thresholds[person_j]:
							avg_j = True
					elif test_beliefs[person_i] < test_beliefs[person_j]:
						# test if i will rise
						if (count_above_i / num_conn_i) >= thresholds[person_i]:
							avg_i = True
						# test if j will drop
						if (count_below_j / num_conn_j) >= thresholds[person_j]:
							avg_j = True
					# no action if equal

					if avg_i: 
						# print "Averaging i to ", ij_avg_belief
						test_beliefs[person_i] = ij_avg_belief
					if avg_j:
						# print "Averaging j to ", ij_avg_belief
						test_beliefs[person_j] = ij_avg_belief

				# ALPHA interaction (forceful)
				elif rand1 > beta_ij and rand1 <= (alpha_ij + beta_ij):
					# i forces j to adjust either:
					#   -to portion of avg of neighbors + i's belief (peer pressure)
					#   -to portion of own belief + i's belief (at random)
					if test_beliefs[person_i] > test_beliefs[person_j]:
						if (count_above_j / num_conn_j) >= thresholds[person_j]:
							test_beliefs[person_j] = thresholds[person_j] * avg_above_j + \
								(1 - thresholds[person_j]) * test_beliefs[person_i]
						elif rand2 >= thresholds[person_j]:
							test_beliefs[person_j] = thresholds[person_j] * test_beliefs[person_j] + \
								(1 - thresholds[person_j]) * test_beliefs[person_i]
					elif test_beliefs[person_i] < test_beliefs[person_j]:
						if (count_below_j / num_conn_j) >= thresholds[person_j]:
							test_beliefs[person_j] = thresholds[person_j] * avg_below_j + \
								(1 - thresholds[person_j]) * test_beliefs[person_i]
						elif rand2 >= thresholds[person_j]:
							test_beliefs[person_j] = thresholds[person_j] * test_beliefs[person_j] + \
								(1 - thresholds[person_j]) * test_beliefs[person_i]

				# GAMMA interaction (identity)
				else:
					pass

			# end interactions (n) loop

			# add results of interactions on beliefs to running sum for this strategy
			strat_sum_beliefs = [(strat_sum_beliefs[i] + tb) \
				for i, tb in enumerate(test_beliefs)]
			
			# record nodes won for this sim 
			for tb in test_beliefs:
				if tb > node_won_thresh:
					strat_sum_nodes_won[0] += 1
				elif tb < -node_won_thresh:
					strat_sum_nodes_won[1] += 1

		# end realizations (k) loop

		# test if this strategy is new best based on payoff
		# if so, update best_strat & best_sum_xxx
		if payoff_type == 0:
			# test if best strat based on agent being evaluated
			if (cur_agent == 0 and sum(strat_sum_beliefs) > sum(best_sum_beliefs)) or \
				(cur_agent == 1 and sum(strat_sum_beliefs) < sum(best_sum_beliefs)):
				# new best strategy is the current one
				best_sum_beliefs = strat_sum_beliefs
				best_strat = ss
		else:
			if strat_sum_nodes_won[cur_agent] > best_sum_nodes_won[cur_agent]:
				best_sum_nodes_won = strat_sum_nodes_won
				best_strat = ss
			
		# disconnect all US/TB test strategies for this loop
		for node in ss:
			miscutils.disconnect(adj_mx, agents[cur_agent], node)
			agent_connects[cur_agent].remove(node)

	# end combine (strategies) loop

	best_option['Strategy'] = best_strat
	best_option['Beliefs'] = [(b / num_realizations) for b in best_sum_beliefs]

	return best_option

# end def getBestStrategy