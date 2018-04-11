import requests

def API_call(user_input):
    try:
        print("testing if zipcode")
        int(user_input)
        # zipcode entered
        print("zipcode API call")
        query = "zip={}"
    except ValueError:
        print("city name API call")
        # city name entered
        user_input = user_input.lower()
        query = "q={}"
    return requests.get('http://api.openweathermap.org/data/2.5/weather?{}&APPID=729e8479b0893cb6745505ba71830535'.format(query.format(user_input)))

def convert_temp(temp, units):
    if units == "metric":
        temp -= 273.15
    elif units == "imperial":
        temp = temp * 9/5 - 459.67
    return int(temp) #removing decimal before returning to keep front-end clean

# formula adapted from https://stackoverflow.com/questions/7490660/converting-wind-direction-in-angles-to-text-words
def degToCompass(num):
    val = int((num / 22.5) + .5)
    arr = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return arr[(val % 16)]