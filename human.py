
import datetime
import dateutil.relativedelta

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.escape
import tornado.websocket

from database import db_conn


class ContributionsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/contributions.html')


class ContributorsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/contributors.html')


class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/dashboard.html')

class DashboardAPIHandler(tornado.web.RequestHandler):
    def get(self):
        now = datetime.datetime.now()
        this_month = datetime.datetime(now.year, now.month, 1)
        print(this_month, this_month.timestamp())
        next_month = this_month + dateutil.relativedelta.relativedelta(months=1)
        print(next_month, next_month.timestamp())

        since = int(next_month.timestamp())
        until = int(this_month.timestamp())

        event_rows = db_conn.iteritems()
        event_rows.seek(b'timeline_%s' % str(until).encode('utf8'))
        events = []
        users = {}
        for event_key, event_id in event_rows:
            if not event_key.startswith(b'timeline_'):
                break
            # print(event_key, event_id)
            event_row = db_conn.get(b'event_%s' % event_id)
            event = tornado.escape.json_decode(event_row)
            # print(event)
            users.setdefault(event['pubkey'], [])
            users[event['pubkey']].append(event)
            # rsp = ["EVENT", subscription_id, event]
            # rsp_json = tornado.escape.json_encode(rsp)
            # self.write_message(rsp_json)

        # for tag in tags:
        #     print(tag)
        #     if tag[0] == 't':
        #         hashed_tag = hashlib.sha256(tag[1].encode('utf8')).hexdigest()
        #         event_rows.seek(b'hashtag_%s' % hashed_tag.encode('utf8'))
        #         for event_key, event_id in event_rows:
        #             if not event_key.startswith(b'hashtag_%s' % hashed_tag.encode('utf8')):
        #                 break
        #             print(event_key, event_id)
        #             event_row = db_conn.get(b'event_%s' % event_id)
        #             event = tornado.escape.json_decode(event_row)
        #             rsp = ["EVENT", subscription_id, event]
        #             rsp_json = tornado.escape.json_encode(rsp)
        #             self.write_message(rsp_json)


        # rsp = ["EOSE", subscription_id]
        # rsp_json = tornado.escape.json_encode(rsp)
        # self.write_message(rsp_json)

        self.finish({'users': users})

