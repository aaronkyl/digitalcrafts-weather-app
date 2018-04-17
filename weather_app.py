import os
import tornado.ioloop
import tornado.web
import tornado.log
import tornado.web
import json
import requests
import queries
from datetime import datetime, timedelta
from helpers import API_call, convert_temp, degToCompass

from jinja2 import Environment, PackageLoader, select_autoescape
  
ENV = Environment(
    loader=PackageLoader('app', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

class TemplateHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.session = queries.Session(
            'postgresql://postgres@localhost:5432/weather')
            
    def render_template(self, tpl, context):
        template = ENV.get_template(tpl)
        self.write(template.render(**context))

class MainHandler(TemplateHandler):
    def get(self):
        units = self.get_query_argument("units", None)
        user_input = self.get_query_argument("user_input", None)
        if user_input:
            cached_weather_data = self.session.query('''
                SELECT weather_data, cached_datetime
                FROM cache
                WHERE location = %(location)s
                ''', {'location': str(user_input).lower()})
            if cached_weather_data:
                # if weather data is old
                if cached_weather_data[0]['cached_datetime'] < datetime.utcnow() - timedelta(minutes=15):
                    # get new weather data
                    current_weather = API_call(user_input).json()
                    # update cache with recent weather data
                    self.session.query('''
                        UPDATE cache 
                        SET weather_data = %(data)s
                          , cached_datetime = current_timestamp
                        WHERE location = %(loc)s
                        ''', {"loc": user_input, "data": json.dumps(current_weather)})
                else:
                    # use cached weather data
                    current_weather = json.loads(cached_weather_data[0]['weather_data'])
            else:
                # no cached weather data
                # get current weather data
                current_weather = API_call(user_input).json()
                # confirm weather data returned
                if current_weather['cod'] == 200:
                    # store weather data in cache
                    self.session.query('''
                        INSERT INTO cache VALUES (%(loc)s, %(data)s, current_timestamp)
                        ''', {"loc": user_input, "data": json.dumps(current_weather)})
                else:
                    # user provided incorrect city or zip
                    self.render_template("home.html", {"message": "City not found"})
                    return 
            
            try:
                current_humidity = current_weather['main']['humidity']
            except:
                current_humidity = None
            
            try:
                current_wind_speed = current_weather['wind']['speed']
                if units == "imperial":
                    current_wind_speed = float("{0:.2f}".format(current_wind_speed * 9/4))
            except KeyError:
                current_wind_speed = None
            
            try:
                current_wind_direction = degToCompass(current_weather['wind']['deg'])
            except KeyError:
                current_wind_direction = None
            
            current_temp = current_weather['main']['temp']
            if current_temp >= 308:
                background = "hot"
            elif current_temp >= 300:
                background = "warm"
            elif current_temp >= 286:
                background = "pleasant"
            elif current_temp >= 273:
                background = "cold"
            else:
                background = "freezing"
            
            condition_background = []
            for condition in current_weather['weather']:
                condition_background.append(condition['id'])
            condition_background.sort()
            if condition_background[0] < 600:
                background += "-rainy"
            elif condition_background[0] < 700:
                background += "-snowy"
            elif condition_background[0] < 800:
                background += "-foggy"
            elif condition_background[0] > 800 and condition_background[0] < 900:
                background += "-cloudy"
            
            
            params = {
                "loc": user_input.title(),
                "units": units,
                "current_temp": convert_temp(current_temp, units),
                "current_humidity": current_humidity,
                "current_wind_speed": current_wind_speed,
                "current_wind_direction": current_wind_direction,
                "conditions": current_weather['weather'],
                "background": background
            }
            
            self.render_template("results.html", params)
        
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