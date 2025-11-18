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
            self.routing_table[neighbor_id] = {}
            print("Adding neighbor ", neighbor_id, " to router",self.router_id,"'s routing table.")
            self.routing_table[neighbor_id]["ip, port"] = (self.neighbor_ip_port_table[neighbor_id])
            self.routing_table[neighbor_id]["next_hop"] = neighbor_id
            self.routing_table[neighbor_id]["cost"] = self.cost_table[neighbor_id]

    def update_routing_table(self):
        for neighbor_id in self.cost_table.keys():
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


    def send_single_update(self, neighbor_id):
        # sends DV to a single neighbor
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # use sendto in udp socket using neighbor IP, port
        data = str(self.cost_table).encode()
        print("type of data is ", type(data))
        print("address is ", self.neighbor_ip_port_table[neighbor_id], "of type", type(self.neighbor_ip_port_table[neighbor_id]))
        print("runnign sendto")
        s.sendto(data, self.neighbor_ip_port_table[neighbor_id])
        print("ran sendto complete")
        s.close()

    def send_updates_to_all_neighbors(self):
        for neighbor_id in self.cost_table.keys():
            print('sending to neighbor ', neighbor_id)
            self.send_single_update(neighbor_id)

    def receive_single_update(self, connection):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            data = connection.recv(1024).decode()
            print(f"Received distance vector update: {data}")
            # data = data.split() # neighbor id, cost
            # self.cost_table[data[0]] = int(data[1])
            # print(f"New distance from {data[0]}: {data[1]}")
            return

    def handle_incoming_update(self, socket):
        # use recvfrom in udp socket
        data, address = socket.recvfrom(1024)
        # decode the received data to string and print out
        data = eval(data.decode()) # bytes to dict
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

    def bellman_ford_update(self, neighbor_id, neighbor_dv):
        # Implement the Bellman-Ford algorithm to update routing table
        # neighbor_dv is a dict mapping destination IDs to costs from neighbor_id
        # update = False
        # dist_to_neighbor = neighbor_dv[self.router_id]


        # Check distance to every destination via this neighbor
        # Distance to this neighbor:
        dist_to_neighbor = min(neighbor_dv[self.router_id], self.get_cost(neighbor_id))

        # Distance looping through all the dests the neighbor knows about
        for dest_id in neighbor_dv.keys():
            print("Checking dest_id ", dest_id, " via neighbor ", neighbor_id)
            current_cost_to_dest = self.cost_table.get(dest_id, float('inf'))
            cost_via_neighbor = dist_to_neighbor + neighbor_dv[dest_id]

            if cost_via_neighbor < current_cost_to_dest:
                self.cost_table[dest_id] = cost_via_neighbor
                self.routing_table[dest_id] = {
                    "next_hop": neighbor_id,
                    "cost": cost_via_neighbor,
                    "ip, port": self.neighbor_ip_port_table.get(neighbor_id, ("", 0))
                }
                print(f"Routing table from {self.router_id} to {dest_id} updated via neighbor {neighbor_id} from cost {current_cost_to_dest} to {cost_via_neighbor}")


        # ## Neighbor DV: {1: cost, 2: cost, ...}
        
        # for dest_id in neighbor_dv.keys():
        #     # distance to dest_id without going through neighbor
        #     current_cost = self.cost_table.get(dest_id, float('inf'))

        #     # distance to dest_id via neighbor
        #     cost_via_neighbor = neighbor_dv[self.router_id] + neighbor_dv[dest_id]

        #     if cost_via_neighbor < current_cost:
        #         self.cost_table[dest_id] = cost_via_neighbor
        #         self.routing_table[dest_id] = {
        #             "next_hop": neighbor_id,
        #             "cost": cost_via_neighbor,
        #             "ip, port": self.neighbor_ip_port_table.get(neighbor_id, ("", 0))
        #         }
        #         update = True
            
        #     if update:
        #         print(f"Routing table from {self.router_id} to {dest_id} \
        #               updated via neighbor {neighbor_id} \
        #               from cost {current_cost} to {cost_via_neighbor}")

          
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