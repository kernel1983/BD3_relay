
import sys
import time
import hashlib
import json
#import multiprocessing
#import threading
#import curses

#import eth_hash.auto
import web3
import eth_account
#import requests

import tornado.ioloop
import tornado.gen
import tornado.websocket

def update_profile(sk):
    a = web3.eth.Account.from_key(hashlib.sha256(sk).hexdigest())
    t = int(time.time())
    c = {
        'name': 'KK',
        'about': 'about',
        'picture': 'picture',
        'role': 'user',
    }
    json_bytes = json.dumps([0, a.address, t, 0, [], c], separators=(',', ':'), ensure_ascii=False)
    event_hash_id = hashlib.sha256(json_bytes.encode('utf8')).hexdigest()

    e = {
        "id": event_hash_id,
        "pubkey": a.address,
        "created_at": t,
        "kind": 0,
        "tags": [],
        "content": c,
    }
    m = eth_account.messages.encode_defunct(text=json_bytes)
    s = a.sign_message(m)
    e['sig'] = s.signature.hex()

    seq = ["EVENT", e]
    msg = json.dumps(seq)
    return msg

class RelayClient:
    def __init__(self, url):
        self.url = url
        self.ioloop = tornado.ioloop.IOLoop.instance()
        self.ws = None
        self.connect()
        #tornado.ioloop.PeriodicCallback(self.keep_alive, 20000).start()
        #tornado.ioloop.PeriodicCallback(self.poll, 500).start()
        self.ioloop.start()

    @tornado.gen.coroutine
    def connect(self):
        #try:
        self.ws = yield tornado.websocket.websocket_connect(self.url)
        msg = update_profile(b'1')
        self.ws.write_message(msg)

        #except Exception:
        #    pass
        self.run()

    @tornado.gen.coroutine
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
            msg = update_profile(str(nonce).encode('utf8'))
            self.ws.write_message(msg)
            nonce += 1
            time.sleep(1)

    #def keep_alive(self):
    #    if self.ws is None:
    #        self.connect()
    #    else:
    #        self.ws.write_message('["KEEP_ALIVE"]')

    #def poll(self):
    #    for conn in cs:
    #        if conn.poll(0.1):
    #            m = conn.recv()
    #            if m[0] == 'DONE':
    #                # continue
    #                commitment = m[3]
    #                end = m[2]
    #                conn.send(['START', end, commitment])
    #                console.log(m)

    #            elif m[0] == 'FOUND':
    #                # submit to chain
    #                console.log(m)

if __name__ == "__main__":
    client = RelayClient("ws://127.0.0.1:8053/relay")

