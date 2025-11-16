import socket
import threading
from router.py import Router

def get_port_id_from_topology(topology_file):
    with open(topology_file, 'r') as f:
        lines = f.readlines()
        mylines = lines[2].split()
        port = int(mylines[2])
        server_id = int(mylines[1])
    return port, server_id


def update_cost(router, neighbor_id, new_cost):
    pass

def user_input_handler():

    while(True):
        user_input = input("Enter command: ")

        if user_input[0:5] == "update":
            args = user_input.split()
            update_cost(router, int(args[1]), int(args[2]))
            pass

        elif user_input == "step":
            pass

        elif user_input == "packets":
            pass

        elif user_input == "display":
            pass

        elif user_input[0:6] == "disable":
            pass

        elif user_input == "crash":
            pass

        elif user_input == "exit":
            break

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
            port,server_id = get_port_id_from_topology(topology_file)
            break
        else: 
            print("Invalid input. Please try again.")
            continue

    # Creat router and start router thread
    router = Router("topology1.txt")
    router_thread = threading.Thread(target=router.run)
    router_thread.start()
    

    # Start user input thread
    input_thread = threading.Thread(target=input_handler)
    input_thread.start()
    input_thread.join()