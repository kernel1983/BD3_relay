
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

class ContributorsAPIHandler(tornado.web.RequestHandler):
    def get(self):
        address_rows = db_conn.iteritems()
        address_rows.seek(b'DAO_lxdao_')
        users = {}
        for address_key, _ in address_rows:
            if not address_key.startswith(b'DAO_lxdao_'):
                break

            address = address_key.decode('utf8').replace('DAO_lxdao_', '')
            users[address] = {}

        self.finish({'users': users})

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
        users = {}
        total = 0
        for event_key, event_id in event_rows:
            if not event_key.startswith(b'timeline_'):
                break
            # print(event_key, event_id)
            event_row = db_conn.get(b'event_%s' % event_id)
            event = tornado.escape.json_decode(event_row)
            qualified = 0
            point = 0
            for tag in event['tags']:
                if tag[0] == 't' and tag[1] == 'lxdao':
                    qualified += 1
                if tag[0] == 't' and tag[1] == 'points':
                    point = int(tag[2])
                    qualified += 1

            if qualified == 2:
                users.setdefault(event['pubkey'], {})
                if 'profile' not in users[event['pubkey']]:
                    profile_json = db_conn.get(b'profile_%s' % (event['pubkey'].encode('utf8')))
                    # print(profile_json)
                    if profile_json:
                        profile = tornado.escape.json_decode(profile_json)
                        users[event['pubkey']]['profile'] = profile

                users[event['pubkey']].setdefault('points', 0)
                users[event['pubkey']]['points'] += point

                total += point

        self.add_header('access-control-allow-origin', '*')
        self.finish({'users': users, 'total': total})

