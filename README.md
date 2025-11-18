# Overview of Project Implementation


# Example command 
`server -t topology1.txt -i 30`

This command creates a server, with parameters set by `topology1.txt` and auto-updates every 30 seconds.


# main.py
Handles user input. Creates a router object and the necessary threads. 

1. The input handler takes user input into the terminal and splits up their arguments as needed. It allows for the commands update, step, packets, display, disable, and crash. It points out invalid input for any other commands typed.
2. Main has a thread for listening.
3. Main has a thread for sending periodic updates. 
4. Main has a thread for taking user inputs. 


# router.py
The router class supports functions of the server, like maintaining a routing and cost table, and sending/receiving messages to/from other servers.

## Routing Table
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

This definition can be found on lines 67-81 of `router.py`

## Update Sending
The function `send_periodic_updates()` loops for the entirety of the program. It waits for the given time interval then sends updates to all of the router's neighbors using the helper function send_single_update. The step command also calls `send_periodic_updates()`.

The update is actually sent by the function `send_single_update()`. It sends an update to the specified neighbor id.
It sends the cost table (insteaad of the longer form shown in the project assignment since we were confused by the diagram).
This contains all of the necessary information for the neighbors to perform DV updates according to the Bellman-Ford algorithm. 

### Cost Table
To implement the cost table of the router we used a dictionary that has server ids as the keys and their associated cost as the value. 

Every time a router receives an update it will run the Bellman-Ford algorithm to determine if the cost table needs to be updated.

The cost table does include a special key-value pair, `"id" : router_id`since this is information that the recipient neighbor needs to run the Bellman-Ford algorithm. There's probably a cleaner way of organizing this, but it works! 

This definition can be found on lines 121-128 of `router.py`.

### 


