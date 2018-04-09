import os
import tornado.ioloop
import tornado.web
import tornado.log
import tornado.web
import json
import requests

from jinja2 import \
    Environment, PackageLoader, select_autoescape
  
ENV = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

class TemplateHandler(tornado.web.RequestHandler):
    def render_template(self, tpl, context):
        template = ENV.get_template(tpl)
        self.write(template.render(**context))

class MainHandler(TemplateHandler):
    def get(self):
        user_input = self.get_query_argument("user_input", None)
        if user_input:
            self.render_template("results.html", {})
        else:
            self.render_template("home.html", {})
        
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (
            r"/static/(.*)",
            tornado.web.StaticFileHandler,
            {'path': 'static'}
        ),
        ], autoreload=True)
  
if __name__ == "__main__":
    tornado.log.enable_pretty_logging()
    app = make_app()
    # setting a static port to allow for database access at same time
    app.listen('8888')
    # app.listen(int(os.environ.get('PORT', '8000')))
    tornado.ioloop.IOLoop.current().start()