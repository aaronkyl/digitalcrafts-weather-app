import os
import tornado.ioloop
import tornado.web
import tornado.log
import tornado.web
import json
import requests

from jinja2 import Environment, PackageLoader, select_autoescape
  
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
        units = self.get_query_argument("units", None)
        user_input = self.get_query_argument("user_input", None)
        if user_input:
            try:
                # zipcode entered
                int(user_input)
                current_weather = requests.get('http://api.openweathermap.org/data/2.5/weather?zip={}&APPID=729e8479b0893cb6745505ba71830535'.format(user_input))
            except ValueError:
                # city name entered
                current_weather = requests.get('http://api.openweathermap.org/data/2.5/weather?q={}&APPID=729e8479b0893cb6745505ba71830535'.format(user_input))
            
            current_weather = current_weather.json()
            
            try:
                current_temp = current_weather['main']['temp']
            except KeyError:
                # city name does not exist
                self.render_template("home.html", {"message": "City not found"})
                return
                
            conditions = current_weather['weather']
            
            if units == "metric":
                current_temp -= 273.15
            elif units == "imperial":
                current_temp = current_temp * 9/5 - 459.67
            else:
                pass
            
            current_temp = "%.1f" % current_temp
            self.render_template("results.html", {"current_temp": current_temp, "units": units, "conditions": conditions})
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