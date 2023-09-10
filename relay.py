
import os
import json
import hashlib

import eth_account

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.escape
import tornado.websocket

import bd3
import database
import console


subscriptions = {}

class RelayHandler(tornado.websocket.WebSocketHandler):
    child_miners = set()

    def check_origin(self, origin):
        return True

    def open(self):
        if self not in RelayHandler.child_miners:
            RelayHandler.child_miners.add(self)

        console.log("RelayHandler connected")


    def on_close(self):
        if self in RelayHandler.child_miners:
            RelayHandler.child_miners.remove(self)

        console.log("RelayHandler disconnected")


    @tornado.gen.coroutine
    def on_message(self, message):
        db_conn = database.get_conn()
        seq = tornado.escape.json_decode(message)
        console.log("RelayHandler", seq)

        if seq[0] == 'REQ':
            subscription_id = seq[1]
            self.filters = seq[2]
            subscriptions[subscription_id] = self

            ids = self.filters.get('ids')
            authors = self.filters.get('authors')
            kinds = self.filters.get('kinds')
            tags = self.filters.get('tags')

            since = self.filters.get('since')
            until = self.filters.get('until')
            limit = self.filters.get('limit')

            event_rows = db_conn.iteritems()
            if authors:
                for author_id in authors:
                    event_rows.seek(b'user_%s' % author_id.encode('utf8'))
                    for event_key, event_id in event_rows:
                        if not event_key.startswith(b'user_'):
                            break
                        console.log(event_key, event_id)
                        event_row = db_conn.get(b'event_%s' % event_id)
                        event = tornado.escape.json_decode(event_row)
                        rsp = ["EVENT", subscription_id, event]
                        rsp_json = tornado.escape.json_encode(rsp)
                        self.write_message(rsp_json)

            elif ids:
                event_rows = []
                for event_id in ids:
                    console.log(event_id)
                    event_row = db_conn.get(b'event_%s' % event_id.encode('utf8'))
                    event = tornado.escape.json_decode(event_row)
                    rsp = ["EVENT", subscription_id, event]
                    rsp_json = tornado.escape.json_encode(rsp)
                    self.write_message(rsp_json)

            elif tags:
                for tag in tags:
                    console.log(tag)
                    if tag[0] == 't':
                        hashed_tag = hashlib.sha256(tag[1].encode('utf8')).hexdigest()
                        event_rows.seek(b'hashtag_%s' % hashed_tag.encode('utf8'))
                        for event_key, event_id in event_rows:
                            if not event_key.startswith(b'hashtag_%s' % hashed_tag.encode('utf8')):
                                break
                            console.log(event_key, event_id)
                            event_row = db_conn.get(b'event_%s' % event_id)
                            event = tornado.escape.json_decode(event_row)
                            rsp = ["EVENT", subscription_id, event]
                            rsp_json = tornado.escape.json_encode(rsp)
                            self.write_message(rsp_json)

            else:
                event_rows.seek(b'timeline_')
                for event_key, event_id in event_rows:
                    if not event_key.startswith(b'timeline_'):
                        break
                    console.log(event_key, event_id)
                    event_row = db_conn.get(b'event_%s' % event_id)
                    console.log(event_row)
                    event = tornado.escape.json_decode(event_row)
                    if event['kind'] == 1:
                        addr = event['pubkey'].lower()
                        profile_json = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
                        # console.log(profile_json)
                        if profile_json:
                            profile = tornado.escape.json_decode(profile_json)
                            event['profile'] = profile

                    rsp = ["EVENT", subscription_id, event]
                    rsp_json = tornado.escape.json_encode(rsp)
                    self.write_message(rsp_json)

            rsp = ["EOSE", subscription_id]
            rsp_json = tornado.escape.json_encode(rsp)
            self.write_message(rsp_json)

        elif seq[0] == 'EVENT':
            event_id = seq[1]['id']
            addr = seq[1]['pubkey']
            timestamp = seq[1]['created_at']
            kind = seq[1]['kind']
            tags = seq[1]['tags']
            content = seq[1]['content']
            # console.log(content)
            sig = seq[1]['sig']
            data = tornado.escape.json_encode(seq[1])

            msg = json.dumps([0, addr, timestamp, kind, tags, content], separators=(',', ':'), ensure_ascii=False)
            message = eth_account.messages.encode_defunct(text=msg)
            # console.log(message)
            sender = eth_account.Account.recover_message(message, signature=bytes.fromhex(sig[2:]))
            console.log(sender, addr)
            assert sender.lower() == addr

            if kind == 0:
                console.log('content', content)
                db_conn.put(b'profile_%s' % (addr.encode('utf8')), tornado.escape.json_encode(content).encode('utf8'))

            elif kind == 1:
                tags = seq[1]['tags']
                for tag in tags:
                    if tag[0] == 't':
                        console.log('t', tag)
                        hashed_tag = hashlib.sha256(tag[1].encode('utf8')).hexdigest()
                        db_conn.put(b'hashtag_%s_%s' % (hashed_tag.encode('utf8'), str(timestamp).encode('utf8')), event_id.encode('utf8'))

                db_conn.put(b'timeline_%s_%s' % (str(timestamp).encode('utf8'), addr.encode('utf8')), event_id.encode('utf8'))
                db_conn.put(b'tweet_%s' % (event_id.encode('utf8'), ), tornado.escape.json_encode({}).encode('utf8'))

            elif kind == 3:
                tags = seq[1]['tags']
                for tag in tags:
                    if tag[0] == 'follow':
                        console.log('follow', tag)

                    elif tag[0] == 'unfollow':
                        console.log('unfollow', tag)

                    elif tag[0] == 'like':
                        console.log('like', tag)
                        tweet_event_id = tag[1]
                        tweet_json = db_conn.get(b'tweet_%s' % (tweet_event_id.encode('utf8'), ))
                        tweet = tornado.escape.json_decode(tweet_json)
                        console.log('tweet', tweet)
                        tweet.setdefault('likes', [])
                        tweet.setdefault('dislikes', [])

                    elif tag[0] == 'dislike':
                        console.log('dislike', tag)
                        tweet_event_id = tag[1]
                        tweet_json = db_conn.get(b'tweet_%s' % (tweet_event_id.encode('utf8'), ))
                        tweet = tornado.escape.json_decode(tweet_json)
                        console.log('tweet', tweet)
                        tweet.setdefault('likes', [])
                        tweet.setdefault('dislikes', [])

                    elif tag[0] == 'unlike':
                        console.log('unlike', tag)
                        tweet_event_id = tag[1]
                        tweet_json = db_conn.get(b'tweet_%s' % (tweet_event_id.encode('utf8'), ))
                        tweet = tornado.escape.json_decode(tweet_json)
                        console.log('tweet', tweet)
                        tweet.setdefault('likes', [])
                        tweet.setdefault('dislikes', [])

                    elif tag[0] == 'attest':
                        console.log('attest', tag)
                        attest_user = tag[1]
                        attest_data = tag[2]
                        schemas = []
                        for i in attest_data:
                            console.log(i)
                            if i[0] == '$' and ':' in i:
                                p = i.index(':')
                                console.log(i[:p])
                                schemas.append(i[:p])
                            else:
                                schemas.append(i)

                        schemas_json = json.dumps(schemas, separators=(',', ':'), ensure_ascii=False)
                        attest_type = hashlib.sha256(schemas_json.encode('utf8')).hexdigest()
                        console.log(attest_type)

                        db_conn.put(('attest_%s_%s_%s' % (addr, attest_user, attest_type)).encode('utf8'), event_id.encode('utf8'))

            console.log('data', data)
            db_conn.put(b'event_%s' % (event_id.encode('utf8'), ), data.encode('utf8'))
            db_conn.put(b'user_%s_%s' % (addr.encode('utf8'), str(timestamp).encode('utf8')), event_id.encode('utf8'))

        elif seq[0] == 'CLOSE':
            pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/profile')

class TimelineHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/timeline.html')

class TweetHandler(tornado.web.RequestHandler):
    def get(self):
        event = self.get_argument('event')
        self.render('static/tweet.html')

class TagHandler(tornado.web.RequestHandler):
    def get(self):
        tag = self.get_argument('tag')
        self.render('static/tag.html')

class ProfileHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/profile.html')

class ProfileAPIHandler(tornado.web.RequestHandler):
    def get(self):
        db_conn = database.get_conn()
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.lower().encode('utf8')))
        console.log(content)

        result = {
            'errno': 0,
            'errMsg': '',
            'data': {}
        }
        if content:
            result['data'] = tornado.escape.json_decode(content)
        self.add_header('access-control-allow-origin', '*')
        self.finish(result)

class FollowingAPIHandler(tornado.web.RequestHandler):
    def get(self):
        db_conn = database.get_conn()
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
        self.add_header('access-control-allow-origin', '*')
        self.finish(tornado.escape.json_decode(content))

class FollowedAPIHandler(tornado.web.RequestHandler):
    def get(self):
        db_conn = database.get_conn()
        addr = self.get_argument('addr')
        content = db_conn.get(b'profile_%s' % (addr.encode('utf8')))
        self.add_header('access-control-allow-origin', '*')
        self.finish(tornado.escape.json_decode(content))

class AttestSchemasAPIHandler(tornado.web.RequestHandler):
    def get(self):
        self.add_header('access-control-allow-origin', '*')
        self.finish({'schemas':
            [ ['I meet offline with', '$user'],
              ['$user', 'is the', '$role', 'of', '$organization'],
              ['$user', 'is the expert of', '$skill'], ]
        })

class TestAPIHandler(tornado.web.RequestHandler):
    def post(self):
        sig = self.request.body
        console.log(sig)
        message = eth_account.messages.encode_defunct(text='abcd')
        console.log(message)
        console.log(eth_account.Account.recover_message(message, signature=bytes.fromhex(sig[2:].decode('utf8'))))
        # console.log((web3.Web3()).eth.account.recover_message(message, signature=bytes.fromhex(sig[2:].decode('utf8'))))


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": './static/'}),
                (r"/relay", RelayHandler),
                (r"/tweet", TweetHandler),
                (r"/tag", TagHandler),
                (r"/timeline", TimelineHandler),
                (r"/profile", ProfileHandler),
                (r"/api/profile", ProfileAPIHandler),
                # (r"/api/following", FollowingAPIHandler),
                # (r"/api/followed", FollowedAPIHandler),
                (r"/api/test", TestAPIHandler),

                # (r"/contributions", bd3.ContributionsHandler),
                # (r"/api/contributors", bd3.ContributorsAPIHandler),
                # (r"/contributors", bd3.ContributorsHandler),
                # (r"/dashboard", bd3.DashboardHandler),
                # (r"/api/dashboard", bd3.DashboardAPIHandler),

                (r"/people", bd3.PeopleHandler),
                (r"/person", bd3.PersonHandler),
                (r"/organization", bd3.OrganizationHandler),
                (r"/organizations", bd3.OrganizationsHandler),
                (r"/need", bd3.NeedHandler),
                (r"/api/persons", bd3.PersonsAPIHandler),
                (r"/api/organizations", bd3.OrganizationsAPIHandler),
                (r"/api/attest_user", bd3.AttestUserAPIHandler),
                (r"/api/attest_event", bd3.AttestEventAPIHandler),
                (r"/api/attest_schemas", AttestSchemasAPIHandler),
                (r"/", MainHandler),
            ]
        settings = {"debug": True}

        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    server = Application()
    server.listen(8053, '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()

