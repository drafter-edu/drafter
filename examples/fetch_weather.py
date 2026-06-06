from drafter import *
import requests

@dataclass
class State:
    lat: str
    lng: str
    
NEWARK_LATITUDE = 39.6782
NEWARK_LONGITUDE = -75.7616
URL = "https://forecast.weather.gov/MapClick.php?lat={}&lon={}&FcstType=json"

def fetch_weather(lat: str, lng: str) -> str:
    params = {
        "lat": lat,
        "lon": lng,
        "FcstType": "json"
    }
    response = requests.get(URL.format(lat, lng))
    data = response.json()
    return data["currentobservation"]["Weather"]
    
@route
def index(state: State) -> Page:
    weather = fetch_weather(state.lat, state.lng)
    
    return Page(
        state,
        [
            "The weather at latitude " + state.lat + " and longitude " + state.lng + " is: " + weather,
            LineBreak(),
            "Enter new coordinates to check the weather there:",
            LineBreak(),
            "Latitude: ", TextBox("lat", state.lat), LineBreak(),
            "Longitude: ", TextBox("lng", state.lng), LineBreak(),
            Button("Check weather", get_weather),
        ]
    )
    

@route
def get_weather(state: State, lat: str, lng: str) -> Page:
    state.lat = lat
    state.lng = lng
    return index(state)


start_server(State(str(NEWARK_LATITUDE), str(NEWARK_LONGITUDE)))