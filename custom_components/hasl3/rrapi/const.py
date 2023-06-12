__version__ = '3.1.1'

BASE_URL = 'https://api.resrobot.se/v2.1/'
STOP_LOOKUP_URL = '{}location.name?input={}&format=json&accessId={}'
ARRIVAL_BOARD_URL = '{}arrivalBoard?id={}&format=json&accessId={}'
DEPARTURE_BOARD_URL = '{}departureBoard?id={}&format=json&accessId={}'
ROUTE_PLANNER_URL = '{}trip?format=json&originId={}&destId={}&passlist=true&showPassingPoints=true&accessId={}'

USER_AGENT = "hasl-rrapi/" + __version__
