import logging
import jsonpickle
import isodate
import time
import sys

from datetime import datetime, timedelta
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.util.dt import now
from .exceptions import HaslException

from custom_components.hasl3.slapi import (
    slapi,
    slapi_fp,
    slapi_tl2,
    slapi_ri4,
    slapi_si2,
    slapi_rp3,
    SLAPI_Error,
    SLAPI_API_Error,
    SLAPI_HTTP_Error
)

logger = logging.getLogger(f"custom_components.hasl3.worker")


class HASLStatus(object):
    """System Status."""
    startup_in_progress = True
    running_background_tasks = False

class HASLData(object):
    tl2 = {}
    si2 = {}
    ri4 = {}
    rp3 = {}
    rp3keys = {}
    si2keys = {}
    ri4keys = {}
    fp = {}
    
    def dump(self):
        return {
            'si2keys': self.si2keys,
            'ri4keys': self.ri4keys,
            'tl2': self.tl2,
            'si2': self.si2,
            'ri4': self.ri4,
            'fp': self.fp
        }    

class HASLInstances(object):
    """The instance holder object object"""

    instances = {}
    instanceCount = 0

    def add(self, id, updater):
        self.instances[id] = {
            'subscriber': updater
        }
        self.instanceCount+=1

    def remove(self, id):
        try:
            self.instances[id]['subscriber']()
            self.instanceCount-=1
            del self.instances[id]
        except Exception as e:
            logger.debug(f"Error occured while unregistering listener {str(e)}")

    def count(self):
        return self.instanceCount  

class HaslWorker(object):
    """HaslWorker."""

    hass = None
    configuration = None
    status = HASLStatus()
    data = HASLData()
    instances = HASLInstances()
    
    @staticmethod
    def init(hass,configuration):
        """Return a initialized HaslWorker object."""
        return HaslWorker()

    def debugdump(self, data):
        logger.debug("[debug_dump] Entered")          

        try:
            timestring = time.strftime("%Y%m%d%H%M%S")
            outputfile = self.hass.config.path(f"hasl_debug_{timestring}.json")
            jsonFile = open(outputfile, "w")
            jsonFile.write(jsonpickle.dumps(data, unpicklable=False))
            jsonFile.close()
            logger.debug("[debug_dump] Completed")          
        except:
            logger.debug("[debug_dump] A processing error occured")          

    def getminutesdiff(self, d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
        d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")
        diff = (d1 - d2).total_seconds()
        logger.debug(f"[get_minutes_diff] diff {diff}, d1 {d1}, d2 {d2}")
        return diff
        
    def checksensorstate(self, sensor,state,default=True):
        logger.debug("[check_sensor_state] Entered")          
        if not sensor is None and not sensor == "":
            try:
                sensor_state = self.hass.states.get(sensor)
                if sensor_state.state is state:
                    logger.debug("[check_sensor_state] Completed will return TRUE/ENABLED")
                    return True
                else:
                    logger.debug("[check_sensor_state] Completed will return FALSE/DISABLED")
                    return False
            except:
                logger.debug("[check_sensor_state] An error occured, default will be returned")
                return default          
        else:
            logger.debug("[check_sensor_state] No sensor specified, will return default")
            return default        

    async def assert_rp3(self, key, source, destination):
        logger.debug("[assert_rp3] Entered")

        listvalue = f"{source}-{destination}"
        if not key in self.data.rp3keys:
            logger.debug("[assert_rp3] Registered key")
            self.data.rp3keys[key] = {
                "api_key": key,
                "trips": ""
            }
        else:
            logger.debug("[assert_rp3] Key already present")
            
        currentvalue = self.data.rp3keys[key]['trips']    
        if currentvalue=="":
            logger.debug("[assert_rp3] Creating trip key")
            self.data.rp3keys[key]["trips"] = listvalue
        else:
            logger.debug("[assert_rp3] Amending to trip key")
            self.data.rp3keys[key]["trips"] = f"{currentvalue}|{listvalue}"

        if not listvalue in self.data.rp3:
            logger.debug("[assert_rp3] Creating default values")
            self.data.rp3[listvalue] = {
                "api_type": "slapi-si2",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending",
                "trips": []
            }

        logger.debug("[assert_rp3] Completed")
        return


    def parseDepartureTime(self, t):
        """ weird time formats from the API,
        do some quick and dirty conversions. """

        try:
            if t == 'Nu':
                return 0
            s = t.split()
            if len(s) > 1 and s[1] == 'min':
                return int(s[0])
            s = t.split(':')
            if len(s) > 1:
                rightnow = now()
                min = int(s[0]) * 60 + int(s[1]) - (rightnow.hour * 60 +
                                                    rightnow.minute)
                if min < 0:
                    min = min + 1440
                return min
        except Exception as e:
            ##TODO LOG EXCEPTION
            return
        return        
        
        
    async def process_rp3(self):
        logger.debug("[process_rp3] Entered")
    
        for rp3key in list(self.data.rp3keys):
            logger.debug(f"[process_rp3] Processing key {rp3key}")
            rp3data = self.data.rp3keys[rp3key]
            api = slapi_rp3(rp3key)
            for tripname in '|'.join(set(rp3data["trips"].split('|'))).split('|'):
                logger.debug(f"[process_rp3] Processing trip {tripname}")
                newdata = self.data.rp3[tripname]
                positions = tripname.split('-')
                
                try:

                    apidata = {}

                    srcLocID = ''
                    dstLocID = ''
                    srcLocLat = ''
                    srcLocLng = ''
                    dstLocLat = ''
                    dstLocLng = ''

                    if "," in positions[0]:
                        srcLoc = positions[0].split(',')
                        srcLocLat = srcLoc[0]
                        srcLocLng = srcLoc[1]
                    else:
                        srcLocID = positions[0]

                    if "," in positions[1]:
                        dstLoc = positions[1].split(',')
                        dstLocLat = dstLoc[0]
                        dstLocLng = dstLoc[1]
                    else:
                        dstLocID = positions[1]

                    apidata = await api.request(srcLocID, dstLocID, srcLocLat, srcLocLng, dstLocLat, dstLocLng)                             
                    newdata['trips'] = []
                    
                    #Parse every trip
                    for trip in apidata["Trip"]:
                        newtrip = {
                            'fares': [],
                            'legs': []
                        }
                                    
                        # Loop all fares and add
                        for fare in trip['TariffResult']['fareSetItem'][0]['fareItem']:
                            newfare = {}
                            newfare['name'] = fare['name']
                            newfare['desc'] = fare['desc']
                            newfare['price'] = int(fare['price'])/100
                            newtrip['fares'].append(newfare)
                        
                        # Add legs to trips
                        for leg in trip['LegList']['Leg']:
                            newleg = {'origin': {}, 'destination': {}, 'messages': []}
                            # New Format
                            newleg['origin']['time'] = f"{leg['Origin']['date']} {leg['Origin']['time']}"
                            if leg['Origin'].get('rtDate') and leg['Origin'].get('rtTime'):
                                newleg['origin']['real_time'] = f"{leg['Origin']['rtDate']} {leg['Origin']['rtTime']}"
                            else:
                                newleg['origin']['real_time'] = None
                            newleg['origin']['name'] = leg['Origin']['name']
                            newleg['origin']['type'] = leg['Origin']['type']
                            newleg['origin']['lon'] = leg['Origin']['lon']
                            newleg['origin']['lat'] = leg['Origin']['lat']
                            newleg['origin']['prognosis_type'] = leg['Origin'].get('prognosisType')
                            newleg['origin']['track'] = leg['Origin'].get('track')
                            newleg['origin']['real_track'] = leg['Origin'].get('rtTrack')

                            newleg['destination']['time'] = f"{leg['Destination']['date']} {leg['Destination']['time']}"
                            if leg['Destination'].get('rtDate') and leg['Destination'].get('rtTime'):
                                newleg['destination']['real_time'] = f"{leg['Destination']['rtDate']} {leg['Destination']['rtTime']}"
                            else:
                                newleg['destination']['real_time'] = None
                            newleg['destination']['name'] = leg['Destination']['name']
                            newleg['destination']['type'] = leg['Destination']['type']
                            newleg['destination']['lon'] = leg['Destination']['lon']
                            newleg['destination']['lat'] = leg['Destination']['lat']
                            newleg['destination']['prognosis_type'] = leg['Destination'].get('prognosisType')
                            newleg['destination']['track'] = leg['Destination'].get('track')
                            newleg['destination']['real_track'] = leg['Destination'].get('rtTrack')
                            
                            if leg.get('Messages', {}).get('Message'):
                                for _message in leg['Messages']['Message']:
                                    message = {}
                                    message['head'] = _message.get('head', '')
                                    message['text'] = _message.get('text', '')
                                    message['category'] = _message.get('category')
                                    message['priority'] = _message.get('priority')
                                    message['active'] = _message.get('act')

                                    if _message.get('sDate') and _message.get('sTime'):
                                        message['start_time'] = f"{_message['sDate']} {_message['sTime']}"
                                    else:
                                        message['start_time'] = None
                                    
                                    if _message.get('eDate') and _message.get('eTime'):
                                        message['end_time'] = f"{_message['eDate']} {_message['eTime']}"
                                    else:
                                        message['end_time'] = None
                                    newleg['messages'].append(message)                            
                            
                            #Walking is done by humans. And robots. Robots are scary.
                            if leg["type"]=="WALK":
                                newleg['name'] = leg['name']
                                newleg['line'] = 'Walk'
                                newleg['direction'] = 'Walk'
                                newleg['category'] = 'WALK'
                            else:
                                newleg['name'] = leg['Product']['name']
                                newleg['line'] = leg['Product']['line']
                                newleg['operator_code'] = leg['Product'].get('operatorCode')
                                newleg['operator'] = leg['Product'].get('operator')
                                newleg['direction'] = leg['direction']
                                newleg['category'] = leg['category']
                            newleg['type'] = leg['type']
                            newleg['prognosis'] = leg['prognosis_type']
                            newleg['from'] = leg['Origin']['name']
                            newleg['to'] = leg['Destination']['name']
                            newleg['time'] = f"{leg['Origin']['date']} {leg['Origin']['time']}" 

                            if leg.get('duration'):
                                newleg['duration'] = str(isodate.parse_duration(leg['duration']))
                            else:
                                newleg['duration'] = None
                            newleg['distance'] = leg.get('dist')

                            # Parse color
                            newleg['color'] = None
                            if newleg['category'] == 'MET':
                                if newleg['line'] in ('10', '11'):
                                     newleg['color'] = 'blue'
                                elif newleg['line'] in ('13', '14'):
                                     newleg['color'] = 'red'
                                elif newleg['line'] in ('17', '18', '19'):
                                     newleg['color'] = 'red'
                            elif newleg['category'] == 'BUS':
                                #check if value contains blå
                                if 'blåbuss' in newleg['name']:
                                    newleg['color'] = 'blue'
                                else:
                                    newleg['color'] = 'red'                            
                            
                            if 'Stops' in leg:
                                newtrip['Stops']
                                for stop in leg['Stops']['Stop']:
                                    newleg['stops'].append(stop)

                            newtrip['legs'].append(newleg)
                            
                        #Make some shortcuts for data
                        newtrip['first_leg'] = newtrip['legs'][0]['name']
                        newtrip['time'] = newtrip['legs'][0]['time']
                        newtrip['price'] = newtrip['fares'][0]['price']
                        if trip.get('duration'):
                            newtrip['duration'] = str(isodate.parse_duration(trip['duration']))
                        else:
                            newtrip['duration'] = None
                        newtrip['transfers'] = trip['transferCount']
                        newdata['trips'].append(newtrip)
                    
                    #Add shortcuts to info in the first trip if it exists
                    firstLegFirstTrip = next((x for x in newdata['trips'][0]['legs'] if x["category"] != "WALK"), [])
                    lastLegLastTrip = next((x for x in reversed(newdata['trips'][0]['legs']) if x["category"] != "WALK"), [])
                    newdata['transfers'] = sum(p["category"] != "WALK" for p in newdata['trips'][0]['legs'])-1 or 0
                    newdata['price'] = newdata['trips'][0]['price'] or ''
                    newdata['time'] = newdata['trips'][0]['time'] or ''
                    newdata['duration'] = newdata['trips'][0]['duration'] or ''
                    newdata['from'] = newdata['trips'][0]['legs'][0]['from'] or ''
                    newdata['to'] = newdata['trips'][0]['legs'][len(newdata['trips'][0]['legs'])-1]['to'] or ''
                    newdata['first_leg'] = firstLegFirstTrip["name"] or ''
                    newdata['first_line'] = firstLegFirstTrip["line"] or ''
                    newdata['first_direction'] = firstLegFirstTrip["direction"] or ''
                    newdata['first_category'] = firstLegFirstTrip["category"] or ''
                    newdata['first_time'] = firstLegFirstTrip["time"] or ''
                    newdata['first_from'] = firstLegFirstTrip["from"] or ''
                    newdata['first_to'] = firstLegFirstTrip["to"] or ''
                    newdata['last_leg'] = lastLegLastTrip["name"] or ''
                    newdata['last_line'] = lastLegLastTrip["line"] or ''
                    newdata['last_direction'] = lastLegLastTrip["direction"] or ''
                    newdata['last_category'] = lastLegLastTrip["category"] or ''
                    newdata['last_time'] = lastLegLastTrip["time"] or ''
                    newdata['last_from'] = lastLegLastTrip["from"] or ''
                    newdata['last_to'] = lastLegLastTrip["to"] or ''
                    
                    newdata['attribution'] = newdata['trips'][0]['operator'] or ''
                    newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                    newdata['api_result'] = "Success"
                except Exception as e:
                    exception_type, exception_object, exception_traceback = sys.exc_info()
                    filename = exception_traceback.tb_frame.f_code.co_filename
                    line_number = exception_traceback.tb_lineno
                    logger.debug(f"[process_rp3] Error occured: {filename} #{str(line_number)} str({exception_type}) {str(e)}")
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)
            
                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.rp3[tripname] = newdata

                logger.debug(f"[process_rp3] Completed trip {tripname}")

            logger.debug(f"[process_rp3] Completed key {rp3key}")

        logger.debug("[process_rp3] Completed")


    async def assert_fp(self, traintype):
        logger.debug("[assert_fp] Entered")

        if not traintype in self.data.fp:
            logger.debug(f"[assert_fp] Registering {traintype}")
            self.data.fp[traintype] = {
                "api_type": "slapi-fp1",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
        else:
            logger.debug(f"[assert_fp] {traintype} already registered")
            
        logger.debug("[assert_fp] Completed")
        return
        
    async def process_fp(self, notarealarg=None):
        logger.debug("[process_rp3] Entered")
        
        api = slapi_fp()
        for traintype in list(self.data.fp):
            logger.debug(f"[process_rp3] Processing {traintype}")

            newdata = self.data.fp[traintype]
            try:
                newdata['data'] = await api.request(traintype)
                newdata['attribution'] = "Stockholms Lokaltrafik"
                newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                newdata['api_result'] = "Success"
                logger.debug(f"[process_rp3] Completed {traintype}")
            except Exception as e:
                newdata['api_result'] = "Error"
                newdata['api_error'] = str(e)
                logger.debug(f"[process_rp3] Error occured for {traintype}: {str(e)}")
            
            newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
            self.data.fp[traintype] = newdata
        logger.debug("[process_rp3] Completed")

    async def assert_si2_stop(self, key, stop):
        await self.assert_si2(key,f"stop_{stop}","stops",stop)

    async def assert_si2_line(self, key, line):
        await self.assert_si2(key,f"line_{line}","lines",line)

    async def assert_si2(self, key, datakey, listkey, listvalue):   
        logger.debug("[assert_si2] Entered")

        if not key in self.data.si2keys:
            logger.debug("[assert_si2] Registering key")
            self.data.si2keys[key] = {
                "api_key": key,
                "stops": "",
                "lines": ""
            }
        else:
            logger.debug("[assert_si2] Key already present")

        if self.data.si2keys[key][listkey]=="":
            logger.debug("[assert_si2] Creating trip key")
            self.data.si2keys[key][listkey] = listvalue
        else:
            logger.debug("[assert_si2] Appending to trip key")
            self.data.si2keys[key][listkey] = f"{self.data.si2keys[key][listkey]},{listvalue}"
            
        if not datakey in self.data.si2:
            logger.debug("[assert_si2] Creating default values")
            self.data.si2[datakey] = {
                "api_type": "slapi-si2",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
            
        logger.debug("[assert_si2] Completed")
        return
        
    async def process_si2(self, notarealarg=None):
        logger.debug("[process_si2] Entered")
    
        for si2key in list(self.data.si2keys):
            logger.debug(f"[process_si2] Processing key {si2key}")
            si2data = self.data.si2keys[si2key]
            api = slapi_si2(si2key, 60)
            for stop in ','.join(set(si2data["stops"].split(','))).split(','):
                logger.debug(f"[process_si2] Processing stop {stop}")
                newdata = self.data.si2[f"stop_{stop}"]
                #TODO: CHECK FOR FRESHNESS TO NOT KILL OFF THE KEYS

                try:
                    deviationdata = await api.request(stop,'')
                    deviationdata = deviationdata['ResponseData']   

                    deviations = []
                    for (idx, value) in enumerate(deviationdata):
                        deviations.append({
                            'updated': value['Updated'],
                            'title': value['Header'],
                            'fromDate': value['FromDateTime'],
                            'toDate': value['UpToDateTime'],
                            'details': value['Details'],
                            'sortOrder': value['SortOrder'],
                            })

                    newdata['data'] = sorted(deviations, key=lambda k: k['sortOrder'])      
                    newdata['attribution'] = "Stockholms Lokaltrafik"
                    newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                    newdata['api_result'] = "Success"
                    logger.debug(f"[process_si2] Processing stop {stop} completed")
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)                
                    logger.debug(f"[process_si2] An error occured during processing of stop {stop}")


                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.si2[f"stop_{stop}"] = newdata
                logger.debug(f"[process_si2] Completed processing of stop {stop}")
                
            for line in ','.join(set(si2data["lines"].split(','))).split(','):
                logger.debug(f"[process_si2] Processing line {line}")
                newdata = self.data.si2[f"line_{line}"]
                #TODO: CHECK FOR FRESHNESS TO NOT KILL OFF THE KEYS

                try:
                    deviationdata = await api.request('',line)
                    deviationdata = deviationdata['ResponseData']   

                    deviations = []
                    for (idx, value) in enumerate(deviationdata):
                        deviations.append({
                            'updated': value['Updated'],
                            'title': value['Header'],
                            'fromDate': value['FromDateTime'],
                            'toDate': value['UpToDateTime'],
                            'details': value['Details'],
                            'sortOrder': value['SortOrder'],
                            })

                    newdata['data'] = sorted(deviations, key=lambda k: k['sortOrder'])      
                    newdata['attribution'] = "Stockholms Lokaltrafik"
                    newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                    newdata['api_result'] = "Success"
                    logger.debug(f"[process_si2] Processing line {line} completed")
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)                
                    logger.debug(f"[process_si2] An error occured during processing of line {line}")

                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.si2[f"line_{line}"] = newdata
                logger.debug(f"[process_si2] Completed processing of line {line}")

            logger.debug(f"[process_si2] Completed processing key {si2key}")

        logger.debug("[process_si2] Completed")
        return

    async def assert_ri4(self, key, stop):
        logger.debug("[assert_ri4] Entered")
        stopkey = str(stop)
    
        if not key in self.data.ri4keys:
            logger.debug("[assert_ri4] Registering key and stop")
            self.data.ri4keys[key] = {
                "api_key": key,
                "stops": stopkey
            }
        else:
            logger.debug("[assert_ri4] Adding stop to existing key")
            self.data.ri4keys[key]["stops"] = f"{self.data.ri4keys[key]['stops']},{stopkey}"
            
        if not stop in self.data.ri4:
            logger.debug("[assert_ri4] Creating default data")
            self.data.ri4[stopkey] = {
                "api_type": "slapi-ri4",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
            
        logger.debug("[assert_ri4] Completed")
        return
        
    async def process_ri4(self, notarealarg=None):
        logger.debug("[process_ri4] Entered")

        iconswitcher = {
            'Buses': 'mdi:bus',
            'Trams': 'mdi:tram',
            'Ships': 'mdi:ferry',
            'Metros': 'mdi:subway-variant',
            'Trains': 'mdi:train',
        }

        for ri4key in list(self.data.ri4keys):
            logger.debug(f"[process_ri4] Processing key {ri4key}")
            ri4data = self.data.ri4keys[ri4key]
            api = slapi_ri4(ri4key, 60)
            for stop in ','.join(set(ri4data["stops"].split(','))).split(','):
                logger.debug(f"[process_ri4] Processing stop {stop}")
                newdata = self.data.ri4[stop]
                #TODO: CHECK FOR FRESHNESS TO NOT KILL OFF THE KEYS
                
                try:
                    departures = []
                    departuredata = await api.request(stop)
                    departuredata = departuredata['ResponseData']

                    for (i, traffictype) in enumerate(['Metros', 'Buses', 'Trains',
                                                    'Trams', 'Ships']):

                        for (idx, value) in enumerate(departuredata[traffictype]):
                            direction = value['JourneyDirection'] or 0
                            displaytime = value['DisplayTime'] or ''
                            destination = value['Destination'] or ''
                            linenumber = value['LineNumber'] or ''
                            expected = value['ExpectedDateTime'] or ''
                            groupofline = value['GroupOfLine'] or ''
                            icon = iconswitcher.get(traffictype, 'mdi:train-car')
                            diff = self.parseDepartureTime(displaytime)
                            departures.append({
                                'line': linenumber,
                                'direction': direction,
                                'departure': displaytime,
                                'destination': destination,
                                'time': diff,
                                'expected': datetime.strptime(
                                    expected, '%Y-%m-%dT%H:%M:%S'
                                ),
                                'type': traffictype,
                                'groupofline': groupofline,
                                'icon': icon,
                                })

                    newdata['data'] = sorted(departures, key=lambda k: k['time'])      
                    newdata['attribution'] = "Stockholms Lokaltrafik"
                    newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                    newdata['api_result'] = "Success"
                    logger.debug(f"[process_ri4] Stop {stop} updated sucessfully")
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)
                    logger.debug(f"[process_ri4] Error occured during update {stop}")
                
                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.ri4[stop] = newdata
                logger.debug(f"[process_ri4] Completed stop {stop}")

            logger.debug(f"[process_ri4] Completed key {ri4key}")

        logger.debug("[process_ri4] Completed")
        return


    async def assert_tl2(self, key):
        logger.debug("[assert_tl2] Entered")

        if not key in self.data.tl2:
            logger.debug("[assert_tl2] Registering key")
            self.data.tl2[key] = {
                "api_type": "slapi-tl2",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
        else:
            logger.debug("[assert_tl2] Key already present")

        logger.debug("[assert_tl2] Completed")
        return

    async def process_tl2(self, notarealarg=None):
        logger.debug("[process_tl2] Entered")
        
        for tl2key in list(self.data.tl2):
            logger.debug(f"[process_tl2] Processing {tl2key}")
            
            newdata = self.data.tl2[tl2key]
            
            statuses = {
                'EventGood': 'Good',
                'EventMinor': 'Minor',
                'EventMajor': 'Closed',
                'EventPlanned': 'Planned',
            }

            # Icon table used for HomeAssistant.
            statusIcons = {
                'EventGood': 'mdi:check',
                'EventMinor': 'mdi:clock-alert-outline',
                'EventMajor': 'mdi:close',
                'EventPlanned': 'mdi:triangle-outline'
            }

            try:         
        
                api = slapi_tl2(tl2key)
                apidata = await api.request()
                apidata = apidata['ResponseData']['TrafficTypes']    

                responselist = {}
                for response in apidata:
                    statustype = ('ferry' if response['Type'] == 'fer' else response['Type'])

                    for event in response['Events']:
                        event['Status'] = statuses.get(event['StatusIcon'])
                        event['StatusIcon'] = \
                            statusIcons.get(event['StatusIcon'])
                    
                    responsedata = {
                        'status': statuses.get(response['StatusIcon']),
                        'status_icon': statusIcons.get(response['StatusIcon']),
                        'events': response['Events']
                    }
                    responselist[statustype] = responsedata

                # Attribution and update sensor data.
                newdata['data'] = responselist
                newdata['attribution'] = "Stockholms Lokaltrafik"
                newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                newdata['api_result'] = "Success"
                logger.debug(f"[process_tl2] Update of {tl2key} succeeded")
            except Exception as e:
                newdata['api_result'] = "Error"
                newdata['api_error'] = str(e)
                logger.debug(f"[process_tl2] Update of {tl2key} failed")
           
            newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
            self.data.tl2[tl2key] = newdata
            logger.debug(f"[process_tl2] Completed {tl2key}")
            
        logger.debug(f"[process_tl2] Completed")
        return            
