
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient
import tornado.gen
import tornado.escape
import tornado.websocket



class ContributionsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/contributions.html')


class ContributorsHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/contributors.html')


class DashboardHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/dashboard.html')

