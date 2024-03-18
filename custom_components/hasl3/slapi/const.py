__version__ = '3.1.3'

FORDONSPOSITION_URL = 'https://api.sl.se/fordonspositioner/GetData?' \
                      'type={}&pp=false&cacheControl={}'

# old https://api.sl.se/api2 ceases to function on 2024-03-15
TRAFIKLAB_URL = 'https://journeyplanner.integration.sl.se/v1/'
# Due to technical reasons, this API is being replaced by SLs Deviations API and will completely stop working on 2024-03-31
SI2_URL = TRAFIKLAB_URL + 'deviations.json?key={}&siteid={}&lineNumber={}'
# Due to technical reasons, this API is being replaced by SLs Deviations API and GTFS Service alerts. It will stop working on 2024-03-31
TL2_URL = TRAFIKLAB_URL + 'trafficsituation.json?key={}'
# This API will be shut down at the end of March 2024. It is replaced by SL’s new transport API.
RI4_URL = TRAFIKLAB_URL + 'realtimedeparturesV4.json?key={}&siteid={}' \
                          '&timeWindow={}'
PU1_URL = TRAFIKLAB_URL + 'typeahead.json?key={}&searchstring={}' \
                          '&stationsonly=False&maxresults=25'
RP3_URL = TRAFIKLAB_URL + 'TravelplannerV3_1/trip.json?key={}&originExtId={}' \
                          '&destExtId={}&originCoordLat={}' \
                          '&originCoordLong={}&destCoordLat={}' \
                          '&destCoordLong={}&Passlist=1'

USER_AGENT = "hasl-slapi/" + __version__
