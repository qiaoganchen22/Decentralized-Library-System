import binascii
import uuid
from cryptography.fernet import Fernet
import hashlib
import json
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request


def decrypt_book(sender_port):  # code to decrypt the book
    response = requests.get(f'http://{sender_port}/get_key')
    key = response.json()['key'].encode()
    response2 = requests.get(f'http://{sender_port}/get_book')
    encrypted_book = response2.json()['encrypted_book'].encode()
    f = Fernet(key)
    book = f.decrypt(encrypted_book).decode()
    return book


class Blockchain:
    def __init__(self):
        self.chain = []  # the blockchain
        self.transaction = []  # adding transactions to the block
        self.request = []  # book request
        self.request_id = []  # request id
        self.book = []  # encrypted book from receiver
        self.book_key = []  # key to unlock encrypted book
        self.nodes = set()  # all the nodes in the network
        self.new_block(previous_hash='0')

    # creating new nodes
    def create_nodes(self, address):
        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Error')

    # creating new transactions
    def new_transaction(self, rid, key):
        self.transaction.append({
            'proof': rid + key
        })
        last_block = self.last_block
        previous_hash = self.hash(last_block)
        self.new_block(previous_hash)

    # making a block and clearing previous details
    def new_block(self, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'transaction': self.transaction,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }
        self.transaction = []  # clearing
        self.request = []
        self.book = []
        self.request_id = []
        self.book_key = []
        self.chain.append(block)
        return block

    # generating a request
    def new_requests(self, sender_port, receiver_port, book_value):
        network = self.nodes
        for x in network:  # goes through the network
            if x == receiver_port:  # if node is the receiver port send request to it
                requests.post(f'http://{x}/set_request', json={
                    'sender_port': sender_port,
                    'receiver_port': receiver_port,
                    'book_value': book_value
                })
            elif x != receiver_port and x != sender_port:  # if node is not receiver port send request id to it
                response = requests.get(f'http://{sender_port}/get_id')
                if response.status_code == 200:
                    requests.post(f'http://{x}/request_id', json={
                        'id': response.json()['id']
                    })
        self.new_book(receiver_port, book_value)
        self.sending_keys_and_books(sender_port, receiver_port)
        self.sending_id(sender_port, receiver_port, book_value)

    def new_book(self, receiver_port, book_value):
        network = self.nodes
        for x in network:  # goes through the network after request if request has been sent
            if x == receiver_port:
                requests.post(f'http://{x}/generate_book', json={  # generates the encrypted book and key
                    'book_value': book_value
                })

    def sending_keys_and_books(self, sender_port, receiver_port):
        network = self.nodes
        for x in network:  # go through network
            if x == sender_port:  # if the node is the sender, send it the book instead of key
                response = requests.get(f'http://{receiver_port}/get_book')
                if response.status_code == 200:
                    requests.post(f'http://{x}/set_book', json={
                        'encrypted_book': response.json()['encrypted_book']
                    })
            elif x != sender_port and x != receiver_port:  # if the node is not the sender, give them the key
                response = requests.get(f'http://{receiver_port}/get_key')
                if response.status_code == 200:
                    requests.post(f'http://{x}/set_key', json={
                        'key': response.json()['key']
                    })

    def sending_id(self, sender_port, receiver_port, book_value):
        network = self.nodes
        for x in network:
            if x == receiver_port:
                response = requests.get(f'http://{sender_port}/get_id')  # if the sender gets book and other gets key
                if response.status_code == 200:
                    requests.post(f'http://{x}/request_id', json={  # sends the receiver node the id
                        'id': response.json()['id']
                    })
                    check = self.proof(sender_port, receiver_port, value=1)  # if proof and consensus is true, send
                    # key to sender port
                    if check:
                        response = requests.get(f'http://{receiver_port}/get_key')
                        if response.status_code == 200:
                            requests.post(f'http://{sender_port}/set_key', json={
                                'key': response.json()['key']
                            })
                            # the nodes checks if the key is valid by decrypting the book
                            # decrypted book should be book_value requested
                            book = decrypt_book(sender_port)
                            if book == book_value:
                                check = self.proof(sender_port, receiver_port, value=2)
                                # after checking the keys with other nodes, if true, add transaction
                                if check:
                                    self.make_transaction(sender_port, receiver_port)

    def make_transaction(self, sender_port, receiver_port):  # making the transaction
        network = self.nodes
        response = requests.get(f'http://{receiver_port}/get_id')
        receiver_id = response.json()['id']
        response = requests.get(f'http://{sender_port}/get_key')
        sender_key = response.json()['key']
        for x in network:
            requests.post(f'http://{x}/new_transaction', json={
                'id': receiver_id,
                'key': sender_key
            })

    # checks the matching keys and rids
    def proof(self, sender_port, receiver_port, value):
        # if id is 1 then it is valid
        if value == 1:
            accepts = 0
            response = requests.get(f'http://{receiver_port}/get_id')
            check_this = response.json()['id']
            network = self.nodes
            for node in network:
                if node != sender_port and node != receiver_port:
                    response = requests.get(f'http://{node}/get_id')
                    compare_this = response.json()['id']
                    # compare the id from receiver_port with other nodes in network
                    if check_this == compare_this:
                        accepts = accepts + 1
            check = self.consensus(sender_port, receiver_port, accepts)
            if check:
                return True
        # if value = 2 check keys, if true key is valid
        if value == 2:
            accepts = 0
            response = requests.get(f'http://{sender_port}/get_key')
            check_this = response.json()['key']
            network = self.nodes
            for node in network:
                if node != sender_port and node != receiver_port:
                    response = requests.get(f'http://{node}/get_key')
                    compare_this = response.json()['key']
                    # compare the key from sender_port with other nodes in network
                    if check_this == compare_this:
                        accepts = accepts + 1
            check = self.consensus(sender_port, receiver_port, accepts)
            if check:
                return True

    # check if 50% agrees
    def consensus(self, sender_port, receiver_port, accepts):
        # count all nodes in network but sender and receiver
        # compare if agree is >= 50%
        total = 0
        network = self.nodes
        for x in network:
            if x != sender_port and x != receiver_port:
                total = total + 1  # counting the numbers of nodes in the server
        if accepts / total > 0.5:  # nodes that agree divided by the nodes in the network
            return True
        else:
            return False

    # generate book key
    def generate_book_keys(self, book_value):
        # code that uses Fernet to generate keys and encrypt the book
        key = Fernet.generate_key()
        ubyte_key = key.decode()
        byte_key = Fernet(key)
        encrypted = byte_key.encrypt(book_value.encode())
        ubyte_encrypted = encrypted.decode()
        self.book.append({'encrypted_book': ubyte_encrypted})
        self.book_key.append({'key': ubyte_key})

    # adds request into the list
    def set_requests(self, sender_port, receiver_port, book_value):
        self.request.append({
            'sender_port': sender_port,
            'receiver_port': receiver_port,
            'book_value': book_value
        })

    # adds encrypted book into list
    def set_books(self, encrypted_book):
        self.book.append({'encrypted_book': encrypted_book})

    # adds key into list
    def set_keys(self, book_key):
        self.book_key.append({'key': book_key})

    # adds request id into list
    def set_request_ids(self, request_id):
        self.request_id.append({'id': request_id})

    # hashing
    @staticmethod
    def hash(block):
        block_hash = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_hash).hexdigest()

    # get last block
    @property
    def last_block(self):
        return self.chain[-1]
