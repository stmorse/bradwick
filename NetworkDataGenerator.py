# NetworkDataGenerator.py
# Create node and link matrices of network, write to JSON
# INPUT: Dataset_vX.csv
# OUTPUT: adj_mx and agents_mx, write to JSON

import csv
import random
import sys
import miscutils

###

# read in sys args as in and out filenames
if (len(sys.argv[1]) > 0):
	in_path = sys.argv[1]
else:
	print "Requires input file"
	quit(0)

if (len(sys.argv[2]) > 0):
	out_path = sys.argv[2]
else:
	print "Requires output file"
	quit(0)

###

# load entire demographic info into memory
demo_data = []
with open(in_path, 'rU') as data:
	reader = csv.DictReader(data)
	demo_data = [row for row in reader]

# "intelligence-directed connections"
known_connections = [
	[14, 5],   # local criminal to neighboring HH
	[14, 3],   # local criminal to neighboring village jirga mem
	[14, 2],   # local criminal to neighboring village jirga mem
	[73, 72],  # district criminal to district warlord
	[73, 70],  # district criminal to bad ulema
	[73, 48],  # district criminal to bad malik
	[73, 11],  # district criminal to bad malik
	[72, 71],  # regional warlord to subgovernor
	[72, 70],  # regional warlord to bad ulema
	[72, 39],  # regional warlord to district jirga member (of local warlords village)
	[72, 40],  # regional warlord to local jirga member (of local warlords village)
	[68, 21],  # police chief to district jirga member (good)
	[68, 22],  # police chief to village jirga member (good)
	[68, 69],  # police chief to good ulema (good)
	[68, 56] ] # police chief to district jirga member(good)

# population sizes
pop_mutable = len(demo_data)
pop_total = pop_mutable + 2 	# 2 for US and TB agents

forceful_list = {   'Khan', 'Jirga', 'Mullah', 'Warlord',
					'Malik', 'Criminal', 'Insurgent' }
forceful_1_list = { 'Khan1', 'Jirga1', 'Mullah1', 'Warlord1', 
					'Governor', 'Police', 'Criminal1', 'Insurgent1' }

# create empty adjacency matrix (zeros)
# leave room for TB and US
adj_mx = [[0 for n in range(pop_total)] for m in range(pop_total)]

# create empty agents matrix (will append agents below)
agents_mx = []

# fill the adj_mx and agents_mx based on demo
for person in demo_data:
	# convert values to numbers
	for key in person:
		if (key == 'Belief'):
			person[key] = round(float(person[key]),2)
		else:
			person[key] = int(person[key])

	node = person['Node']
	vil = person['Village']
	clus = person['Cluster']
	#belief = person['Belief']
	#belief = round(random.random() - 0.5, 2)
	belief = -.5

	# determine category
	fsum = sum(int(v) for k, v in person.iteritems() if k in forceful_list)
	f1sum = sum(int(v) for k, v in person.iteritems() if k in forceful_1_list)
	if f1sum > 0:
		category = 'Forceful_1'
	elif fsum > 0:
		category = 'Forceful'
	else:
		category = 'Regular'

	# add this person to agents (0 for belief)
	agent = { 'Node': node, 'Type': category, 
			  'Village': vil, 'Cluster': clus, 'Belief': belief }
	agents_mx.append(agent)

	# specify agent connections in adj_mx:
	# -loop across rest of population, 
	# -estab connections based on demog assumptions
	for person2 in demo_data:
		# convert values to numbers
		for key2 in person2:
			if (key2 == 'Belief'):
				person2[key2] = round(float(person2[key2]), 2)
			else:
				person2[key2] = int(person2[key2])

		node2 = person2['Node']
		vil2 = person2['Village']
		clus2 = person2['Cluster']

		relation = False

		# skip if person==person2
		if node == node2:
			continue

		# establish any intra-village links
		if vil == vil2 and (person['Head of Household'] >= 1 or
						   person['Malik'] >= 1 or
						   person['Mullah'] >= 1):
			relation = True

		# malik
		if person['Malik'] >= 1:
			# knows subgovernor and district police chief
			if person2['Governor'] >= 1 or person2['Police'] >= 1:
				relation = True
			# knows other maliks in village cluster
			elif clus == clus2 and person2['Malik'] >= 1:
				relation = True

		# mullah
		if person['Mullah'] >= 1:
			# knows district mullah (ulema)
			if person2['Mullah1'] >= 1:
				relation = True
			# knows other mullahs in cluster
			elif clus == clus2 and person2['Mullah'] >= 1:
				relation = True

		# khan
		if person['Khan'] >= 1:
			# knows khan of cluster (tribal elder)
			if clus == clus2 and person2['Khan1'] >= 1:
				relation = True

		# district jirga
		if person['Jirga1'] >= 1:
			# knows governor, district mullah, dis jirga
			if person2['Governor'] >= 1 or person2['Mullah1'] >= 1 or person2['Jirga1'] >= 1:
				relation = True

		# local warlord (commander)
		if person['Warlord'] >= 1:
			# knows the district commanders
			if person2['Warlord1'] >= 1:
				relation = True

		# local criminal
		if person['Criminal'] >= 1:
			# knows regional criminals
			if person2['Criminal1'] >= 1:
				relation = True

		if relation:
			adj_mx[node][node2] = 1
			adj_mx[node2][node] = 1

	# end person2 in demo loop
# end person in demo loop

# add all "intelligence-driven" connections
for kc in known_connections:
	adj_mx[kc[0]][kc[1]] = 1
	adj_mx[kc[1]][kc[0]] = 1

# add one each US and TB agent
US_agent = { 'Node': len(agents_mx), 'Type':'Forceful_2',
		    'Village': 100, 'Cluster': 100, 'Belief': .5 }
TB_agent = { 'Node': len(agents_mx)+1, 'Type':'Forceful_2',
		    'Village': 100, 'Cluster': 100, 'Belief': -.5 }

agents_mx.append(US_agent)
agents_mx.append(TB_agent)

if len(agents_mx) != pop_total:
	print "Population error: ", len(agents_mx), pop_total

###

# convert agents_mx and adj_mx to JSON and write to output file
miscutils.networkToJSON(agents_mx, adj_mx, out_path)

print "Complete."

# end
