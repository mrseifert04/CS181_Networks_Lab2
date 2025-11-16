import sys

class Router:
    def __init__(self, router_id):
        self.router_id = router_id
        self.routing_table = {}
        self.cost_table = {} # mapping neighbor IDs to integer costs
        self.neighbor_ip_port_table = {} # mapping neighbor IDs to (IP, port) tuples
        self.server_port = None
        self.num_neighbors = 0

    def set_server_port(self, port):
        self.server_port = port

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

        self.num_neighbors = int(lines[0]) - 1

        for i in range(2, 3 + self.num_neighbors):
            neighbor_id, neighbor_ip, neighbor_port = lines[i].split()
            self.neighbor_ip_port_table[int(neighbor_id)] = (neighbor_ip, int(neighbor_port))

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
            
    def update_cost(self, neighbor_id, new_cost):
        if neighbor_id in self.cost_table:
            self.cost_table[neighbor_id] = new_cost
        else:
            print(f"Neighbor {neighbor_id} not found.")

    def display(self):
        print(f"Routing Table for Router {self.router_id}:")
        print("Destination\tNext Hop\tCost")
        for destination in sorted(self.routing_table.keys()):
            next_hop = self.routing_table[destination]["next_hop"]
            cost = self.routing_table[destination]["cost"]
            print(f"{destination}\t\t{next_hop}\t\t{cost}")


    # def add_route(self, destination, next_hop):
    #     self.routing_table[destination] = next_hop

    # def remove_route(self, destination):
    #     if destination in self.routing_table:
    #         del self.routing_table[destination]

    # def get_next_hop(self, destination):
    #     return self.routing_table.get(destination, None)

    # def __str__(self):
    #     return f"Router {self.router_id} Routing Table: {self.routing_table}"

def main(): # run python3 router.py <router_id> <topology_file_path>
    new_router = Router(int(sys.argv[1]))
    print("Made new router with ID ", new_router.router_id)
    new_router.open_topology_file(sys.argv[2])
    # print("Cost table: ", new_router.cost_table)
    # print("IP-Port table: ", new_router.neighbor_ip_port_table)
    new_router.build_routing_table()
    # print("Router's updated routing table: ", new_router.routing_table)
    new_router.display()

if __name__ == "__main__":
    main()