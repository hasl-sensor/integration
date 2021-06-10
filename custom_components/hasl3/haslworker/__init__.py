import logging
import jsonpickle
import isodate
import time

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

    instances = []

    def add(self, id):
        self.instances.append(id)

    def remove(self, id):
        self.instances.remove(id)

    def count(self):
        return len(self.instances)
    

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
        timestring = time.strftime("%Y%m%d%H%M%S")
        outputfile = self.hass.config.path(f"hasl_debug_{timestring}.json")
        jsonFile = open(outputfile, "w")
        jsonFile.write(jsonpickle.dumps(data, unpicklable=False))
        jsonFile.close()
        
    def getminutesdiff(self, d1, d2):
        d1 = datetime.strptime(d1, "%Y-%m-%d %H:%M:%S")
        d2 = datetime.strptime(d2, "%Y-%m-%d %H:%M:%S")
        return abs((d2 - d1).seconds)
        
    def checksensorstate(self, sensor,state,default=True):
        if not sensor is None and not sensor == "":
            sensor_state = self.hass.states.get(sensor)
            if sensor_state.state is state:
                return True
            else:
                return False
        else:
            return default        

    async def assert_rp3(self, key, source, destination):
        listvalue = f"{source}-{destination}"
        if not key in self.data.rp3keys:
            self.data.rp3keys[key] = {
                "api_key": key,
                "trips": ""
            }
            
        currentvalue = self.data.rp3keys[key]['trips']    
        if currentvalue=="":
            self.data.rp3keys[key]["trips"] = listvalue
        else:
            self.data.rp3keys[key]["trips"] = f"{currentvalue},{listvalue}"

        if not listvalue in self.data.rp3:
            self.data.rp3[listvalue] = {
                "api_type": "slapi-si2",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending",
                "trips": []
            }

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
        except Exception:
            ##TODO LOG EXCEPTION
            return
        return        
        
        
    async def process_rp3(self):
    
        for rp3key in list(self.data.rp3keys):
            rp3data = self.data.rp3keys[rp3key]
            api = slapi_rp3(rp3key)
            for tripname in ','.join(set(rp3data["trips"].split(','))).split(','):
                newdata = self.data.rp3[tripname]
                positions = tripname.split('-')
                
                try:
                    apidata = await api.request(positions[0], positions[1], '', '', '', '')                             
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
                            newleg = {}
                            #Walking is done by humans. And robots. Robots are scary.
                            if leg["type"]=="WALK":
                                newleg['name'] = leg['name']
                                newleg['line'] = 'Walk'
                                newleg['direction'] = 'Walk'
                                newleg['category'] = 'WALK'
                            else:
                                newleg['name'] = leg['Product']['name']
                                newleg['line'] = leg['Product']['line']                            
                                newleg['direction'] = leg['direction']
                                newleg['category'] = leg['category']
                            newleg['from'] = leg['Origin']['name']
                            newleg['to'] = leg['Destination']['name']
                            newleg['time'] = f"{leg['Origin']['date']} {leg['Origin']['time']}"                        
                            newtrip['legs'].append(newleg)
                            
                        #Make some shortcuts for data    
                        newtrip['first_leg'] = newtrip['legs'][0]['name']
                        newtrip['time'] = newtrip['legs'][0]['time']
                        newtrip['price'] = newtrip['fares'][0]['price']
                        newtrip['duration'] = str(isodate.parse_duration(trip['duration']))
                        newtrip['transfers'] = trip['transferCount']
                        newdata['trips'].append(newtrip)
                    
                    #Add shortcuts to info in the first trip if it exists
                    newdata['transfers'] = newdata['trips'][0]['transfers'] or 0
                    newdata['price'] = newdata['trips'][0]['price'] or ''
                    newdata['time'] = newdata['trips'][0]['time'] or ''
                    newdata['duration'] = newdata['trips'][0]['duration'] or ''
                    newdata['first_leg'] = newdata['trips'][0]['first_leg'] or ''
                    
                    newdata['attribution'] = "Stockholms Lokaltrafik"
                    newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                    newdata['api_result'] = "Success"
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)
            
                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.rp3[tripname] = newdata



    async def assert_fp(self, traintype):
        if not traintype in self.data.fp:
            self.data.fp[traintype] = {
                "api_type": "slapi-fp1",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
        return
        
    async def process_fp(self, notarealarg=None):
        
        api = slapi_fp()
        for traintype in list(self.data.fp):

            newdata = self.data.fp[traintype]
            try:
                newdata['data'] = await api.request(traintype)
                newdata['attribution'] = "Stockholms Lokaltrafik"
                newdata['last_updated'] = now().strftime('%Y-%m-%d %H:%M:%S')
                newdata['api_result'] = "Success"
            except Exception as e:
                newdata['api_result'] = "Error"
                newdata['api_error'] = str(e)
            
            newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
            self.data.fp[traintype] = newdata

    async def assert_si2_stop(self, key, stop):
        await self.assert_si2(key,f"stop_{stop}","stops",stop)

    async def assert_si2_line(self, key, line):
        await self.assert_si2(key,f"line_{line}","lines",line)

    async def assert_si2(self, key, datakey, listkey, listvalue):   
        if not key in self.data.si2keys:
            self.data.si2keys[key] = {
                "api_key": key,
                "stops": "",
                "lines": ""
            }
            
        if self.data.si2keys[key][listkey]=="":
            self.data.si2keys[key][listkey] = listvalue
        else:
            self.data.si2keys[key][listkey] = f"{self.data.si2keys[key][listkey]},{listvalue}"
            
        if not datakey in self.data.si2:
            self.data.si2[datakey] = {
                "api_type": "slapi-si2",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
            
        return
        
    async def process_si2(self, notarealarg=None):
    
        for si2key in list(self.data.si2keys):
            si2data = self.data.si2keys[si2key]
            api = slapi_si2(si2key, 60)
            for stop in ','.join(set(si2data["stops"].split(','))).split(','):
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
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)                

                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.si2[f"stop_{stop}"] = newdata
                
            for line in ','.join(set(si2data["lines"].split(','))).split(','):
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
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)                

                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.si2[f"line_{line}"] = newdata

        return

    async def assert_ri4(self, key, stop):
        stopkey = str(stop)
    
        if not key in self.data.ri4keys:
            self.data.ri4keys[key] = {
                "api_key": key,
                "stops": stopkey
            }
        else:
            self.data.ri4keys[key]["stops"] = f"{self.data.ri4keys[key]['stops']},{stopkey}"
            
        if not stop in self.data.ri4:
            self.data.ri4[stopkey] = {
                "api_type": "slapi-ri4",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
            
        return
        
    async def process_ri4(self, notarealarg=None):

        iconswitcher = {
            'Buses': 'mdi:bus',
            'Trams': 'mdi:tram',
            'Ships': 'mdi:ferry',
            'Metros': 'mdi:subway-variant',
            'Trains': 'mdi:train',
        }

        for ri4key in list(self.data.ri4keys):
            ri4data = self.data.ri4keys[ri4key]
            api = slapi_ri4(ri4key, 60)
            for stop in ','.join(set(ri4data["stops"].split(','))).split(','):
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
                                'expected': datetime.datetime.strptime(
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
                except Exception as e:
                    newdata['api_result'] = "Error"
                    newdata['api_error'] = str(e)
                
                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.ri4[stop] = newdata
        return


    async def assert_tl2(self, key):
        if not key in self.data.tl2:
            self.data.tl2[key] = {
                "api_type": "slapi-tl2",
                "api_lastrun": '1970-01-01 01:01:01',
                "api_result": "Pending"
            }
        return

    async def process_tl2(self, notarealarg=None):
        
        for tl2key in list(self.data.tl2):
            
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
            except Exception as e:
                newdata['api_result'] = "Error"
                newdata['api_error'] = str(e)
            dispatcher_send(self.hass, "tl2_data_update")
            
            newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
            self.data.tl2[tl2key] = newdata
            
        return            