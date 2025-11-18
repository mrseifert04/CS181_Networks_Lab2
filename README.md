# Overview of Project Implementation


# Example command 
This command creates a server, with parameters set by topology1.txt and auto-updates every 30 seconds
server -t topology1.txt -i 30

## main.py
Handles user input. Creates a router object and starts a thread for it to listen for messages from other servers and a thread to send periodic updates. 

1. The input handler takes user input into the terminal and splits up their arguments as needed. It allows for the commands update, step, packets, display, disable, and crash. It points out invalid input for any other commands typed.
2. The router has an associated thread for listening. 


## router.py
The router class supports functions of the server, like maintaining a routing and cost table, and sending/receiving messages to/from other servers.

### Routing Table
To implement our routing table we used a dictionary of dictionaries:
for Router A, its routing table would be
{
    router_id_B : {
        "ip, port": ip_B, port_B
        "next_hop": besth_hop_to_get_to_B
        "cost": best_cost_A_to_B
    }, 
    router_id_C : {
        "ip, port": ip_C, port_C
        "next_hop": besth_hop_to_get_to_C
        "cost": best_cost_A_to_C
    }, 
    etc
}
This definition can be found on lines 67-81 of router.py


### Update Sending
The function `send_periodic_updates()` loops for the entirety of the program. It waits for the given time interval then sends updates to all of the router's neighbors w
nitnuf eht ht

### 


