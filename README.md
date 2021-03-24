# Decentralized-Library-System

## To run
1. Python 3.6+
2. Install pipenv
```
$ pip install pipenv 
```
3. Install requirements  
```
$ pipenv install 
``` 
4. Run the server:
    * `$ python network.py` 
    * `$ python network.py -p 5001`
    * `$ python network.py -p 5002`
    * `$ python network.py -p 5003`


## Logic 

- I am using a key and id system
- If there are 4 ports 5000,5001,5002,and 5003 in the network
- 5000 would generates a request id and sends a request to 5001. 
- 5000 would also send the request id to 5002 and 5003 but not to 5001. 
- 5001 generates an encrypted book 
- 5001 sends 5002 and 5003 the key and sends 5000 the encrypted book 
- 5000 receives the encrypted book and sends 5001 the request-id 
- 5001 then sends the request id to 5002 and 5003
- The system checks if the request id matches
- If the ids match 5001 sends 5000 the encrypted key and 5000 uses the key to decrypt the book 
- 5000 would then send the key to 5002 and 5003
- The system checks if the key and id matches for everyone else on the network >50% agrees(consensus) 
- if everything matches then this request would be converted into a transaction and added into the chain of transaction 

## Consensus
Needs to have more than 50% of the network to agree.

## Proof of work
Is comparing the keys and ids of all the nodes in the network.

## Create nodes with - new_nodes 

{     
"nodes":["http://127.0.0.1:5000"] 
} 

changing 5000 to 5001, 5002, 5003 for 4 nodes 
## Make a request with - new_request 

{     
"sender_port": "127.0.0.1:5000",     
"receiver_port": "127.0.0.1:5001",     
"book_value": "2" 
} 

## get the chain with - get_chain 
