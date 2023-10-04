
import sys
import time
import hashlib
import json

import web3
import eth_account
#import requests

import tornado.ioloop
import tornado.gen
import tornado.websocket


def new_tweet(sk):
    a = web3.Account.from_key(hashlib.sha256(sk).hexdigest())
    t = int(time.time())
    c = 'new_tweet'
    k = 1
    json_bytes = json.dumps([0, a.address, t, k, [], c], separators=(',', ':'), ensure_ascii=False)
    event_hash_id = hashlib.sha256(json_bytes.encode('utf8')).hexdigest()

    e = {
        "id": event_hash_id,
        "pubkey": a.address,
        "created_at": t,
        "kind": k,
        "tags": [],
        "content": c,
    }
    m = eth_account.messages.encode_defunct(text=json_bytes)
    s = a.sign_message(m)
    e['sig'] = s.signature.hex()

    seq = ["EVENT", e]
    return event_hash_id, seq


def reply_tweet(sk, event_id):
    a = web3.Account.from_key(hashlib.sha256(sk).hexdigest())
    t = int(time.time())
    c = 'reply_tweet'
    k = 1
    tags = [ ['r', event_id, event_id] ]
    json_bytes = json.dumps([0, a.address, t, k, tags, c], separators=(',', ':'), ensure_ascii=False)
    event_hash_id = hashlib.sha256(json_bytes.encode('utf8')).hexdigest()

    e = {
        "id": event_hash_id,
        "pubkey": a.address,
        "created_at": t,
        "kind": k,
        "tags": tags,
        "content": c,
    }
    m = eth_account.messages.encode_defunct(text=json_bytes)
    s = a.sign_message(m)
    e['sig'] = s.signature.hex()

    seq = ["EVENT", e]
    return event_hash_id, seq


class RelayClient:
    def __init__(self, url):
        self.url = url
        self.ws = None
        self.connect()
        #tornado.ioloop.PeriodicCallback(self.keep_alive, 20000).start()
        #tornado.ioloop.PeriodicCallback(self.poll, 500).start()

    @tornado.gen.coroutine
    def connect(self):
        #try:
        self.ws = yield tornado.websocket.websocket_connect(self.url)

        event_id, msg_seq = new_tweet(b'1')
        msg = json.dumps(msg_seq)
        self.ws.write_message(msg)

        event_id, msg_seq = reply_tweet(b'2', event_id)
        msg = json.dumps(msg_seq)
        self.ws.write_message(msg)

        #except Exception:
        #    pass
        self.run()

    def run(self):
        nonce = 2
        while True:
            #msg = yield self.ws.read_message()
            #print(msg)
            #if msg is None:
            #    self.ws = None
            #    break
            #else:
            #    seq = json.loads(msg)

            #msg = update_profile(str(nonce).encode('utf8'))
            #self.ws.write_message(msg)
            nonce += 1
            time.sleep(1)


if __name__ == "__main__":
    client = RelayClient("ws://127.0.0.1:8053/relay")
    tornado.ioloop.IOLoop.instance().start()

