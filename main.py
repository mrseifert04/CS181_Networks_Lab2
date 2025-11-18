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
        # try:
            myrouter.update_cost(int(args[1]), int(args[3]))
        # except:
        #     print("update Error updating cost.")
        #     continue
            print("update SUCCESS")

        elif user_input == "step":
        #try:
            myrouter.send_updates_to_all_neighbors()
        #except:
            # print("step Error sending router update.")
            # continue
            print("step SUCCESS")

        elif user_input == "packets":
            try:
                packets = myrouter.get_num_packets_sent()
                print("Total packets sent: ", packets)
            except:
                print("packets Error retrieving packet count.")
                continue
            print("packets SUCCESS")

        elif user_input == "display":
            try:
                myrouter.display()
            except:
                print("display Error displaying routing table.")
                continue
            print("display SUCCESS")

        elif user_input[0:6] == "disable":
            args = user_input.split()
            try:
                myrouter.remove_route(int(args[1]))
            except:
                print("disable Error disabling link.")
                continue
            print("disable SUCCESS")

        elif user_input == "crash":
            try:
                for i in myrouter.num_neighbors:
                    myrouter.remove_route(myrouter.neighbor_ids[i])
            except:
                print("crash Error crashing router.")
                continue
            print("crash SUCCESS")
            exit()

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
    listening_thread = threading.Thread(target=myrouter.handle_incoming_update, args=(myrouter.listening_socket,))
    
    # Start listening thread
    # listening_thread = threading.Thread(target=handle_connection, args=(myrouter.listening_socket,))
    listening_thread.start()

    # Start user input thread
    input_thread = threading.Thread(target=user_input_handler, args=(myrouter,))
    input_thread.start()

    while(input_thread.is_alive()):
        pass
    exit()

main()



# Example command to run the server with topology file and router ID
# server -t topology1.txt -i 3