import threading
from router import Router

# def get_port_id_from_topology(topology_file):
#     with open(topology_file, 'r') as f:
#         lines = f.readlines()
#         mylines = lines[2].split()
#         port = int(mylines[2])
#         server_id = int(mylines[1])
#     return port, server_id

def initialize_router(filepath):
    myrouter = Router()
    myrouter.open_topology_file(filepath)
    # myrouter.set_server_port() # TODO: this should throw an error or smth if run too early
    myrouter.build_routing_table()
    return myrouter

# def handle_connection(socket):
#     while True:
#         # use recvfrom in udp socket
#         data, address = socket.recvfrom(1024)
#         # decode the received data to string and print out
#         message = data.decode()
#         print(f"Received distance vector update: {data}")

#         #check for updates

def user_input_handler(myrouter):

    while(True):
        user_input = input("Enter command: ")

        if user_input[0:6] == "update":
            # <server1-id> <server1-id> <new_cost>
            args = user_input.split()
            server1_id = int(args[1])
            server2_id = int(args[2])
            new_cost = int(args[3])
            try: 
                if (server1_id == myrouter.router_id):
                    myrouter.update_cost(server2_id, new_cost)
                    myrouter.send_neighbor_update(server2_id, new_cost)
                elif (server2_id == myrouter.router_id):
                    myrouter.update_cost(server1_id, new_cost)
                    myrouter.send_neighbor_update(server1_id, new_cost)
                else:
                    myrouter.send_link_update(server1_id, server2_id, new_cost)
            except:
                print("update Error updating cost.")
                continue
            print("update SUCCESS")

        elif user_input == "step":
            # try:
            myrouter.send_updates_to_all_neighbors()
            # except:
            #     print("step Error sending router update.")
            #     continue
            # print("step SUCCESS")

        elif user_input == "packets":
        
            packets = myrouter.packets_received
            print("Total packets received since last packets command: ", packets)
            myrouter.packets_received = 0 # reset when this command is invoked}
            # except:
            #     print("packets Error retrieving packet count.")
            #     continue
            print("packets SUCCESS")

        elif user_input == "display":
            try:
                myrouter.display()
            except:
                print("display Error displaying routing table.")
                continue
            print("display SUCCESS")

        elif user_input[0:7] == "disable":
            args = user_input.split()
            try:
                neighbor_id = int(args[1])
                if (myrouter.is_neighbor(neighbor_id)):
                    myrouter.update_cost(neighbor_id, float('inf'))
                    myrouter.send_neighbor_update(neighbor_id, float('inf'))
                else:
                    print("disable Error: Server is not a neighbor")
                
            except:
                print("disable Error disabling link")
                continue
            print("disable SUCCESS")

        elif user_input == "crash":
            try:
                for neighbor in myrouter.neighbor_ip_port_table.keys():
                    myrouter.update_cost(neighbor, float('inf'))
                    myrouter.send_neighbor_update(neighbor, float('inf'))
            except:
                print("crash Error failed to crash router")
                continue
            print("crash SUCCESS")

        else:
            print("Invalid input. Please try again.")

        pass

def main():

    # Get server configuration from user
    while(True):
        server_input = input("Please enter server configuration.").split()
        if server_input[0] == "server":
            topology_file = server_input[2]
            routing_update_interval = int(server_input[4])
            break
        
        else: 
            print("Invalid input. Please try again.")
            continue

    myrouter = initialize_router(topology_file)

    # start listening for updates
    listening_thread = threading.Thread(target=myrouter.handle_incoming_update, args=(myrouter.listening_socket,))
    listening_thread.start()

    # start sending periodic updates
    update_thread = threading.Thread(target=myrouter.send_periodic_updates, args=(routing_update_interval,))
    update_thread.start()

    # Start user input thread
    input_thread = threading.Thread(target=user_input_handler, args=(myrouter,))
    input_thread.start()
    input_thread.join()

    exit()

main()



# Example command to run the server with topology file and router ID
# server -t topology1.txt -i 30