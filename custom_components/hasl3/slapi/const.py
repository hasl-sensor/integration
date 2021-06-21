__version__ = '3.0.0-beta.3'
VERSION = __version__

FORDONSPOSITION_URL = 'https://api.sl.se/fordonspositioner/GetData?' \
                      'type={}&pp=false&cacheControl={}'

TRAFIKLAB_URL = 'https://api.sl.se/api2/'
SI2_URL = TRAFIKLAB_URL + 'deviations.json?key={}&siteid={}&lineNumber={}'
TL2_URL = TRAFIKLAB_URL + 'trafficsituation.json?key={}'
RI4_URL = TRAFIKLAB_URL + 'realtimedeparturesV4.json?key={}&siteid={}' \
                          '&timeWindow={}'
PU1_URL = TRAFIKLAB_URL + 'typeahead.json?key={}&searchstring={}' \
                          '&stationsonly=False&maxresults=25'
RP3_URL = TRAFIKLAB_URL + 'TravelplannerV3_1/trip.json?key={}&originExtId={}' \
                          '&destExtId={}&originCoordLat={}' \
                          '&originCoordLong={}&destCoordLat={}' \
                          '&destCoordLong={}'

USER_AGENT = "hasl-slapi/"+VERSION