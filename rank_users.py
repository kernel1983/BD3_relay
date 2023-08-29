
import hashlib
import pprint

import web3
import requests

sk = hashlib.sha256(b'ranker').hexdigest()
a = web3.eth.Account.from_key(sk)
print(sk)
print(a.address)

req = requests.get('http://127.0.0.1:8053/api/persons')
# pprint.pprint(req.json())

req = requests.get('http://127.0.0.1:8053/api/attest_user?addr=%s' % a.address)

pprint.pprint(req.json())

