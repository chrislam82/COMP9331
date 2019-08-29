# zID: z3460499
# Last Modified: 11/08/2019
# Assignment
# Link state routing protocol implementation

# Run using Python3.7.3 (Available on CSE via VLAB)
# python3 COMP9331_Ass1.py config*.txt

from socket import *
import sys
import time

class router_data:
	# Initialise router with data from config.txt
	def __init__ (self, data):
		self.UPDATE_INTERVAL = 1 # Broadcast my LSA every UPDATE_INTERVAL second
		self.ROUTE_UPDATE_INTERVAL = 30 # Run determine_routes() every ROUTE_UPDATE_INTERVAL seconds
		self.ROUTER_FAILURE = 5	 # Fail a neighbouring router if it has not sent a LSA for ROUTER_FAILURE seconds

		data = data.replace("\n", ' ')
		data = data.replace("\t", ' ')
		split_data = data.split(' ')
		while True: # Remove any empty strings in list caused by unexpected formatting
			try:
				split_data.remove('')
			except:
				break
		self.name = split_data[0]
		self.port = int(split_data[1])

		self.neighbours = {} # Dictionary with neighbours and their ports
		self.links = {} # Dictionary that stores LSAs received from all nodes in topology
		self.LSA = [self.name, str(time.time())] # Initialise this router's LSA to its name and current time
		self.links[self.name] = {"timestamp": self.LSA[1], "links": set()} # Initialise topology {A: {"timestamp": 123, "links": {(neighbour, cost), ...}}}

		for neighbour in range(3, len(split_data), 3):
			self.neighbours[split_data[neighbour]] = int(split_data[neighbour + 2]) # Add neighbour from config.txt into neighbours
			self.LSA += [split_data[neighbour], str(split_data[neighbour + 1])] # Add to LSA
			self.links[self.name]["links"].add((split_data[neighbour], float(split_data[neighbour + 1]))) # Add as my own link
			self.links[split_data[neighbour]] = {"timestamp": float(self.LSA[1]), "links": set()} # Initialise entry for neighbour in topology

	# Check for any failed neighbours
	def check_neighbour_fail (self):
		for node in list(self.neighbours.keys()):
			if self.links[node]["timestamp"] < time.time() - self.ROUTER_FAILURE: # if havn't received LSA for set seconds, consider router as failed
				self.neighbours.pop(node) # Remove neighbour so that they are no longer broadcasted to
				self.links.pop(node) # Remove neighbour from topology
				for link in self.links[self.name]["links"]: # Find my link to it and remove it
					if link[0] == node:
						self.links[self.name]["links"].remove(link)
						break
				pos = self.LSA.index(node) # Remove my link to the failed neighbour
				self.LSA = self.LSA[0:pos] + self.LSA[(pos + 2):]

	# Run dijkstras to determine routes from router to all connected routers
	def determine_routes (self):
		try:
			dijkstras = {} # Initialise Dictionary for storing Dijkstra table
			dijkstras_set = set() # Initialise set with router name

			# Initialise Dijkstras with 1st hop neighbours
			for neighbour_link in self.links[self.name]["links"]:
				if neighbour_link[0] in self.links: # Link valid only if router is active in topology
					dijkstras[neighbour_link[0]] = (neighbour_link[1], self.name)

			# And check that a key exists before adding into dijkstras
			while (dijkstras_set != dijkstras.keys()): # Iterate until no more paths available
				smallest = None
				next_node = None

				# Determine which router in dijkstras that is not in set has lowest cost
				for node in dijkstras:
					if node not in dijkstras_set:
						if not smallest or dijkstras[node][0] < smallest:
							smallest = dijkstras[node][0]
							next_node = node

				# Once I do, then we add that into the set
				dijkstras_set.add(next_node)
				for neighbour in self.links[next_node]["links"]:
					if neighbour[0] != self.name and neighbour[0] in self.links:
						node = neighbour[0]
						cost_through_next_node = dijkstras[next_node][0] + neighbour[1]
						# Add node if not stored in dijkstras or cost thorugh this next_node is smaller than previous value
						if node not in dijkstras or cost_through_next_node < dijkstras[node][0]:
							dijkstras[node] = (cost_through_next_node, next_node)

			print ("I am Router", self.name)
			for node in sorted(dijkstras):
				path_cost = dijkstras[node][0]
				predecessor = dijkstras[node][1]
				path = node
				print (f"Least cost path to router {node}:", end = '')
				while predecessor != self.name:
					path = predecessor + path
					predecessor = dijkstras[predecessor][1]
				print (f"{self.name + path} and the cost is {round(dijkstras[node][0], 1)}")
			print ("")
		except:
			# To account for potential unaccounted behaviour
			# 	Force function to exit rather than crash
			pass

with open(sys.argv[1], "r") as file:
	data = file.read()
	file.close()
	router = router_data(data) # Initialise using self.__init__

	socket = socket(AF_INET, SOCK_DGRAM) # IPv4 and UDP socket
	socket.bind(('localhost', router.port))
	current = time.time()
	routing_timer = current

	while True: # Repeating loop approximately every UPDATE_INTERVAL seconds
		# 1. Broadcast my LSA
		router.check_neighbour_fail() # Check for failed neighbours
		timestamp = time.time()
		router.LSA[1] = str(timestamp) # Update my LSA with latest timestamp before broadcast
		message = ' '.join([router.name] + router.LSA)
		for node in router.neighbours:
			socket.sendto(message.encode('utf-8'), ('localhost', router.neighbours[node]))

		# 2. Check dijkstras
			# Run if ROUTE_UPDATE_INTERVAL seconds has passed since last Link state routing output
		if current >= routing_timer + router.ROUTE_UPDATE_INTERVAL:
			router.determine_routes()
			routing_timer += router.ROUTE_UPDATE_INTERVAL

		# 3. Process queue and forward LSAs with remaining time allocated to while loop
		while time.time() < current + 1:
			remainder = current + 1 - time.time()
			socket.settimeout(remainder) # Wait a maximum of remainder seconds for LSAs
			try:
				# Process the received LSA and its headers
				message, neighbour = socket.recvfrom(4096)
				process_msg = message.decode('utf-8').split(' ')
				print (process_msg)
				sender = process_msg[0]
				sender_port = neighbour[1]
				source = process_msg[1]
				source_time = float(process_msg[2]) # LSA timestamp

				# 1. Check for new/rejoining routers
					# Routers are only considered as rejoining if an LSA generated by them is received
				if source not in router.links: # Then we have a router rejoining
					if router.name not in process_msg: # If a router claims to be connected to me, I wait for a personal LSA
						router.links[source] = {"timestamp": 0, "links": set()}
					elif sender == source: # Then the rejoining router is a neighbour
						pos = process_msg.index(router.name)
						router.links[router.name]["links"].add((source, float(process_msg[pos + 1]))) # Add link on my side
						router.LSA += [source, process_msg[pos + 1]] # Add back to my LSA
						router.neighbours[source] = sender_port
						router.links[source] = {"timestamp": 0, "links": set()}
					else:
						continue # Any other unexpected case in which case ignore LSA

				# 2. Check timestamp
				if router.links[source]["timestamp"] < source_time: # Then this is an updated LSA
					router.links[source]["timestamp"] = source_time
					new_links = set()
					for link in range(3, len(process_msg), 2):
						new_links.add((process_msg[link], float(process_msg[link + 1])))
					# Check for any failed non-neighbour routers by differencing old links vs new links
					deleted_links = router.links[source]["links"] - new_links
					# For any links that no longer exist, assume that router has failed
						# Ignore neighbours; Only remove neighbours through check_neighbour_fail()
					for link in deleted_links:
						if link[0] in router.links and link[0] not in router.neighbours:
							router.links.pop(link[0])
					router.links[source]["links"] = new_links # Update topology for source with received LSA

					process_msg[0] = router.name # Modify sender header in received LSA
					message = ' '.join(process_msg)
					for node in router.neighbours: # Then forward it to all neighbours except the sender and source
						if node != sender and node != source: 
							socket.sendto(message.encode('utf-8'), ('localhost', router.neighbours[node]))
			except Exception:
				pass
		current += router.UPDATE_INTERVAL # Refresh allocated to loop for next UPDATE_INTERVAL