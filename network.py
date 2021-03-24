import binascii
import uuid
from cryptography.fernet import Fernet
import hashlib
import json
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
from main import Blockchain

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()


# adding new node
@app.route('/new_nodes', methods=['POST'])
def new_nodes():
    x = request.get_json()
    y = x.get('nodes')
    if y is None:
        return "Error", 400
    for node in y:
        blockchain.create_nodes(node)
    response = {
        'message': "Node created",
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201


# creating the transaction
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    x = request.get_json()
    y = ['id', 'key']
    if not all(keys in x for keys in y):
        return 'Transaction invalid', 400

    blockchain.new_transaction(x['id'], x['key'])
    response = {'message': "New transaction made"}
    return jsonify(response)


# generating request id and request
@app.route('/new_request', methods=['POST'])
def new_request():
    x = request.get_json()
    y = ['sender_port', 'receiver_port', 'book_value']
    if not all(keys in x for keys in y):
        return 'Missing request info', 400

    blockchain.set_request_ids(uuid4())
    blockchain.new_requests(x['sender_port'],
                            x['receiver_port'],
                            x['book_value']),
    response = {'message': f"Request for {x['receiver_port']} completed and added to blockchain"}
    return jsonify(response), 201


# set request
@app.route('/set_request', methods=['POST'])
def set_request():
    x = request.get_json()
    required = ['sender_port', 'receiver_port', 'book_value']
    if not all(keys in x for keys in required):
        return 'Missing request info', 400

    blockchain.set_requests(x['sender_port'],
                            x['receiver_port'],
                            x['book_value'])
    response = {'message': f"Request sent to {x['receiver_port']}"}
    return jsonify(response), 201


# set book
@app.route('/set_book', methods=['POST'])
def set_book():
    x = request.get_json()
    y = ['encrypted_book']
    if not all(keys in x for keys in y):
        return 'Missing request info', 400

    blockchain.set_books(x['encrypted_book'])
    response = {'message': "Book sent"}
    return jsonify(response), 200


# set request id
@app.route('/request_id', methods=['POST'])
def set_request_id():
    x = request.get_json()
    y = ['id']
    if not all(keys in x for keys in y):
        return 'Missing request info', 400

    blockchain.set_request_ids(x['id'])
    response = {'message': "id sent"}
    return jsonify(response), 201


# set book key
@app.route('/set_key', methods=['POST'])
def set_key():
    x = request.get_json()
    y = ['key']
    if not all(keys in x for keys in y):
        return 'Missing request info', 400

    blockchain.set_keys(x['key'])
    response = {'message': "Key sent"}
    return jsonify(response), 201


# generate book
@app.route('/generate_book', methods=['POST'])
def generate_book():
    x = request.get_json()
    y = ['book_value']
    if not all(keys in x for keys in y):
        return 'Missing request info', 400

    blockchain.generate_book_keys(x['book_value'])
    response = {'message': "Book and keys generated"}
    return jsonify(response), 201


# get the encrypted book
@app.route('/get_book', methods=['GET'])
def get_book():
    x = {
        'encrypted_book': blockchain.book[0]['encrypted_book']
    }
    return jsonify(x), 200


# get key
@app.route('/get_key', methods=['GET'])
def get_key():
    x = {
        'key': blockchain.book_key[0]['key']
    }
    return jsonify(x), 200


# get id
@app.route('/get_id', methods=['GET'])
def get_id():
    x = {
        'id': blockchain.request_id[0]['id']
    }
    return jsonify(x), 200


# get request
@app.route('/get_request', methods=['GET'])
def get_request():
    x = {
        'sender_port': blockchain.request[0]['sender_port'],
        'receiver_port': blockchain.request[0]['receiver_port'],
        'book_value': blockchain.request[0]['book_value']
    }
    return jsonify(x), 200


# getting chain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    x = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(x), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen to')
    args = parser.parse_args()
    port = args.port
    app.run(host='127.0.0.1', port=port)
