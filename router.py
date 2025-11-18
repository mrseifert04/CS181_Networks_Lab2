import sys
import socket

class Router:
    def __init__(self):
        self.router_id = None
        self.routing_table = {}
        self.cost_table = {} # mapping neighbor IDs to integer costs
        self.neighbor_ip_port_table = {} # mapping neighbor IDs to (IP, port) tuples
        self.server_port = None
        self.listening_socket = None
        self.num_neighbors = 0

    def set_server_port(self):
        self.server_port = self.neighbor_ip_port_table[self.router_id][1]

    def get_cost(self, neighbor_id):
        # returns cost if neighbor exists, else infinity
        return self.cost_table.get(neighbor_id, float('inf'))
    
    def is_neighbor(self, neighbor_id):
        return (neighbor_id in self.cost_table)

    def open_topology_file(self, filename):
        with open(filename, 'r') as f:
            topology = f.read()
        self.set_initial_topology(topology)
    
    def set_initial_topology(self, topology):
        # topology is a plain text file mapping neighbor IDs to costs
        lines = topology.strip().split('\n')

        self.router_id = int(lines[-1].split()[0]) # second line is this router's ID

        self.num_neighbors = int(lines[0]) - 1

        for i in range(2, 3 + self.num_neighbors):
            neighbor_id, neighbor_ip, neighbor_port = lines[i].split()
            self.neighbor_ip_port_table[int(neighbor_id)] = (neighbor_ip, int(neighbor_port))

        self.server_port = self.neighbor_ip_port_table[self.router_id][1]
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listening_socket.bind(("", self.server_port))

        for i in lines[self.num_neighbors + 3:]: # start reading edges after global vars
            server_id, neighbor_id, cost = i.split()

            self.cost_table[int(neighbor_id)] = int(cost)

            if int(neighbor_id) == self.router_id:
                raise ValueError("Topology file should not set self as neighbor")
            
        self.cost_table["id"] = self.router_id

        # Format of topology.txt:
            # num total routers
            # num edges
            # 1 #placeholderIP
            # 2 #placeholderIP  
            # 3 #placeholderIP
            # 4 #placeholderIP
            # server ID, neighbor ID, cost
            # server ID, neighbor ID, cost
            # server ID, neighbor ID, cost

    def build_routing_table(self):

        # format of routing table: for each ID in increasing order,
        # <destination-server-ID> <next-hop-server-ID> <cost-of-path>
        # routing table is a dictionary of dictionaries, mapping server IDs to next hops and costs

        for neighbor_id in self.cost_table.keys():
            if neighbor_id == "id":
                continue
            else:
                self.routing_table[neighbor_id] = {}
                print("Adding neighbor ", neighbor_id, " to router",self.router_id,"'s routing table.")
                self.routing_table[neighbor_id]["ip, port"] = (self.neighbor_ip_port_table[neighbor_id])
                self.routing_table[neighbor_id]["next_hop"] = neighbor_id
                self.routing_table[neighbor_id]["cost"] = self.cost_table[neighbor_id]

    def update_routing_table(self):
        for neighbor_id in self.cost_table.keys():
            if neighbor_id == "id":
                continue
            else:
                self.routing_table[neighbor_id]["cost"] = self.cost_table[neighbor_id]

    def update_cost(self, neighbor_id, new_cost):
        if neighbor_id in self.cost_table:
            self.cost_table[neighbor_id] = new_cost
            self.update_routing_table()
        else:
            print(f"Neighbor {neighbor_id} not found.")

    def display(self):
        print(f"Routing Table for Router {self.router_id}:")
        print("Destination\tNext Hop\tCost")
        for destination in sorted(self.routing_table.keys()):
            next_hop = self.routing_table[destination]["next_hop"]
            cost = self.routing_table[destination]["cost"]
            print(f"{destination}\t\t{next_hop}\t\t{cost}")

    def send_neighbor_update(self, neighbor_id, new_cost):
        # sends updated link cost to a single neighbor
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = f"link {neighbor_id} {new_cost}".encode()
        s.sendto(data, self.neighbor_ip_port_table[neighbor_id]) 
        s.close()

    def send_link_update(self, server_id1, server_id2, new_cost):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data1 = f"link {server_id1} {new_cost}".encode()
        data2 = f"link {server_id2} {new_cost}".encode()
        s.sendto(data1, self.neighbor_ip_port_table[server_id2]) 
        s.sendto(data2, self.neighbor_ip_port_table[server_id1])
        s.close()

    def send_single_update(self, neighbor_id):
        # sends DV to a single neighbor
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # use sendto in udp socket using neighbor IP, port
        # self.cost_table["id"] = self.router_id
        data = str(self.cost_table).encode()
        s.sendto(data, self.neighbor_ip_port_table[neighbor_id])
        s.close()

    def send_updates_to_all_neighbors(self):
        for neighbor_id in self.cost_table.keys():
            if neighbor_id == "id": 
                continue
            else:
                print('Sending DV update to neighbor ', neighbor_id)
                self.send_single_update(neighbor_id)

    # def receive_single_update(self, connection):
    #     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     while True:
    #         data = connection.recv(1024).decode()
    #         print(f"Received distance vector update: {data}")
    #         # data = data.split() # neighbor id, cost
    #         # self.cost_table[data[0]] = int(data[1])
    #         # print(f"New distance from {data[0]}: {data[1]}")
    #         return

    def handle_incoming_update(self, socket):
        # use recvfrom in udp socket
        data, address = socket.recvfrom(1024)
        data = data.decode()

        # check if we just want to update a link cost
        if (data.split()[0] == "link"):
            data = data.split()
            self.update_cost(int(data[1]), int(data[2]))
            
        # or if we need are receiving a distance vector update
        else: 
            data = eval(data) # bytes to dict
            print(f"Received distance vector update: {data} from {address}")

            print("IN HANDLER, data keys are", data.keys())
            for dest in data.keys():
                print("IN HANDLER, checking dest", dest)
                self.bellman_ford_update(dest, data)

            print("HANDLER FINISHED")

        # for neighbor_id in self.cost_table.keys():
        #     if neighbor_id in data.keys(): # TODO CHECK THIS
        #         self.bellman_ford_update(neighbor_id, data)
        #     else:
        #         print(f"Neighbor ID {neighbor_id} not in received distance vector.")


    def handle_incoming_update(self, socket):
        # use recvfrom in udp socket
        data, address = socket.recvfrom(1024)
        # decode the received data to string and print out
        data = eval(data.decode()) # bytes to dict
        print(f"Received distance vector update: {data} from Router {data["id"]}")
        print("IN HANDLER, data keys are", data.keys())

        for destination_id in data.keys():
    
            if destination_id == "id":
                # used only to send the sender's own ID
                continue 
            elif destination_id == self.router_id:

                # # when sender A sends to recipient B, A's distance to B is 
                # communicated as B's distance to A
               
                # cost measured by recipient
                current_cost = self.cost_table.get(data["id"], float('inf'))
                print("distance measured by recipient is", current_cost)
                # cost measured by sender
                cost_via_neighbor = data[self.router_id]
                print("distance measured by recipient is", cost_via_neighbor)

                # no changes to hops for this one
                self.cost_table[data["id"]] = min(current_cost, cost_via_neighbor)
                self.routing_table[data["id"]]["cost"] = min(current_cost, cost_via_neighbor)

            else:
    
                current_cost = self.cost_table.get(destination_id, float('inf'))
                print("current cost is", current_cost)
                cost_via_neighbor = self.cost_table.get(data["id"]) + data[destination_id]
                print("to neighbor is", self.cost_table.get(data["id"]))
                print("from neighbor to dest is", data[destination_id])
                print("total via neighbor is", cost_via_neighbor)

                if cost_via_neighbor < current_cost:
                    self.cost_table[destination_id] = cost_via_neighbor
                    self.routing_table[destination_id] = {
                        "next_hop": data["id"],
                        "cost": cost_via_neighbor,
                        "ip, port": self.neighbor_ip_port_table.get(data["id"], ("", 0))
                    }
                    print(f"Routing table from {self.router_id}")
                          
        
    # def bellman_ford_update(self, neighbor_id, neighbor_dv):
    #     # Implement the Bellman-Ford algorithm to update routing table
    #     # neighbor_dv is a dict mapping destination IDs to costs from neighbor_id
    #     # update = False
    #     # dist_to_neighbor = neighbor_dv[self.router_id]


    #     # Check distance to every destination via this neighbor
    #     # Distance to this neighbor:
    #     dist_to_neighbor = min(neighbor_dv[self.router_id], self.get_cost(neighbor_id))

    #     # Distance looping through all the dests the neighbor knows about
    #     for dest_id in neighbor_dv.keys():
    #         print("Checking dest_id ", dest_id, " via neighbor ", neighbor_id)
    #         if dest_id == "id":
    #             print("found id key", dest_id)
    #             continue
    #         elif dest_id == self.router_id:
    #             # when sender A sends to recipient B, A's distance to B is 
    #             # communicated as B's distance to A
    #             sender = neighbor_dv["id"]
    #             current_cost_to_dest = self.cost_table.get(sender, float('inf'))
    #             cost_via_neighbor = dist_to_neighbor
    #         else: 
    #             current_cost_to_dest = self.cost_table.get(dest_id, float('inf'))
    #             cost_via_neighbor = dist_to_neighbor + neighbor_dv[dest_id]

    #         if cost_via_neighbor < current_cost_to_dest:
    #             self.cost_table[dest_id] = cost_via_neighbor
    #             self.routing_table[dest_id] = {
    #                 "next_hop": neighbor_id,
    #                 "cost": cost_via_neighbor,
    #                 "ip, port": self.neighbor_ip_port_table.get(neighbor_id, ("", 0))
    #             }
    #             print(f"Routing table from {self.router_id} to {dest_id} updated via neighbor {neighbor_id} from cost {current_cost_to_dest} to {cost_via_neighbor}")

    # def bellman_ford_update(self, sender_id, sender_costs):
    #         # Implement the Bellman-Ford algorithm to update routing table
    #         # neighbor_dv is a dict mapping destination IDs to costs from neighbor_id
    #         # update = False
    #         # dist_to_neighbor = neighbor_dv[self.router_id]

    #         # Check distance to every destination via this neighbor
    #         # Distance to this neighbor:
    #         dist_to_neighbor = min(sender_costs[self.router_id], self.get_cost(sender_id))

    #         for destination_id in sender_costs.keys():
    #             print("BF Checking distance to", destination_id, "via neighbor", sender_id)
    #             current_cost = self.cost_table.get(destination_id, float('inf'))
    #             cost_via_neighbor = dist_to_neighbor + sender_costs[destination_id]

    #             if cost_via_neighbor < current_cost:
    #                 self.cost_table[destination_id] = cost_via_neighbor
    #                 self.routing_table[destination_id] = {
    #                     "next_hop": sender_id,
    #                     "cost": cost_via_neighbor,
    #                     "ip, port": self.neighbor_ip_port_table.get(sender_id, ("", 0))
    #                 }




          
def main(): # run python3 router.py <router_id> <topology_file_path>
    new_router = Router(int(sys.argv[1]))
    print("Made new router with ID ", new_router.router_id)
    new_router.open_topology_file(sys.argv[2])
    print("Cost table: ", new_router.cost_table)
    print("IP-Port table: ", new_router.neighbor_ip_port_table)
    new_router.build_routing_table()
    # print("Router's updated routing table: ", new_router.routing_table)
    new_router.display()

if __name__ == "__main__":
    main()