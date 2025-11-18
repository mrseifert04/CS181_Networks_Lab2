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
        self.packets_received = 0

    def set_server_port(self):
        self.server_port = self.neighbor_ip_port_table[self.router_id][1]

    def get_cost(self, neighbor_id):
        # returns cost if neighbor exists, else infinity
        return self.cost_table.get(neighbor_id, float('inf'))
    
    def is_neighbor(self, neighbor_id):
        return (neighbor_id in self.neighbor_ip_port_table.keys())

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
        data = f"link {self.router_id} {new_cost}".encode()
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
                # print('Sending DV update to neighbor ', neighbor_id)
                self.send_single_update(neighbor_id)

    def send_periodic_updates(self, time_interval):
        import time
        while True:
            time.sleep(time_interval)
            self.send_updates_to_all_neighbors()


    def handle_incoming_update(self, socket):
        while True:
            # use recvfrom in udp socket
            data, address = socket.recvfrom(1024)
            data = data.decode()


            # check if we just want to update a link cost
            if (data.split()[0] == "link"):
                data = data.split()
                neighbor_id = int(data[1])
                cost = data[2]
                if (cost == 'inf'):
                    self.update_cost(neighbor_id, float(cost))
                else:
                    self.update_cost(neighbor_id, float(cost))
                
            # or if we need are receiving a distance vector update
            else:
                data = data.replace("inf", "float('inf')")
                data = eval(data) # bytes to dict
                # decode the received data to string and print out
                print("data received is", data)
        
                
                print(f"RECEIVED A MESSAGE FROM SERVER {data["id"]}")
                self.packets_received +=1

                for destination_id in data.keys():
            
                    if destination_id == "id":
                        # used only to send the sender's own ID
                        continue 
                    elif destination_id == self.router_id:

                        # # when sender A sends to recipient B, A's distance to B is 
                        # communicated as B's distance to A
                    
                        # cost measured by recipient
                        current_cost = self.cost_table.get(data["id"], float('inf'))

                        # cost measured by sender
                        cost_via_neighbor = data[self.router_id]

                        # no changes to hops for this one
                        self.cost_table[data["id"]] = min(current_cost, cost_via_neighbor)
                      
                        self.routing_table[data["id"]]["cost"] = min(current_cost, cost_via_neighbor)
                        print(f"Current cost {current_cost} vs via-neighbor cost {cost_via_neighbor}. No reroute.")

                    else:
                        
                        current_cost = self.cost_table.get(destination_id, float('inf'))
                        cost_via_neighbor = self.cost_table.get(data["id"]) + data[destination_id]

                        if cost_via_neighbor < current_cost:
                            self.cost_table[destination_id] = cost_via_neighbor
                            self.routing_table[destination_id] = {
                                "next_hop": data["id"],
                                "cost": cost_via_neighbor,
                                "ip, port": self.neighbor_ip_port_table.get(data["id"], ("", 0))
                            }
                            # print(f"Routing table from {self.router_id}")
                            print(f"Current cost {current_cost} vs via-neighbor cost {cost_via_neighbor}. Rerouted through {data["id"]}.")
                      
                        else:
                            print(f"Current cost {current_cost} vs via-neighbor cost {cost_via_neighbor}. No reroute.")
           

          
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