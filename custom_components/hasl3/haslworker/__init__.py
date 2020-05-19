"""HASL Worker Process that knows it all"""
import json
import uuid
from datetime import datetime
import time
import jsonpickle

from datetime import timedelta
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.util.dt import now
from custom_components.hasl3.haslworker.exceptions import HaslException
from custom_components.hasl3.slapi import (
    slapi,
    slapi_fp,
    slapi_tl2,
    slapi_ri4,
    slapi_si2,
    SLAPI_Error,
    SLAPI_API_Error,
    SLAPI_HTTP_Error
)

from integrationhelper import Logger
from queueman import QueueManager


class HaslStatus(object):
    """System Status."""
    startup = True
    background_task = False


class HaslSystem(object):
    """System info."""
    status = HaslStatus()
    config_type = None
    config_path = None
    ha_version = None
    disabled = False

class SLAPIHolder(object):
    tl2 = {}
    si2 = {}
    ri4 = {}
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

    
class HaslWorker(object):
    """HaslWorker."""

    logger = Logger("hasl")
    system = HaslSystem()
    queue = QueueManager()    
    hass = None
    version = None
    configuration = None
    recuring_tasks = []
    data = SLAPIHolder()

    @staticmethod
    def init(hass):
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

    async def startup_tasks(self):
        """Tasks tha are started after startup."""
        self.system.status.background_task = True
        self.hass.bus.async_fire("hasl/status", {})

        self.recuring_tasks.append(
            async_track_time_interval(
                self.hass, self.prosess_queue, timedelta(minutes=10)
            )
        )
        
        self.hass.bus.async_fire("hasl/reload", {"force": True})
        await self.prosess_queue()

        self.system.status.startup = False
        self.system.status.background_task = False

        self.hass.bus.async_fire("hasl/status", {})

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
        for traintype in self.data.fp:

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
    
        for si2key in self.data.si2keys:
            si2data = self.data.si2keys[si2key]
            api = slapi_si2(si2key, 60)
            for stop in ','.join(set(si2data["stops"].split(','))).split(','):
                newdata = self.data.si2[f"stop_{stop}"]
                #TODO: CHECK FOR FRESHNESS TO NOT KILL OFF THE KEYS

                #try
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
                #except Exception as e:
                #    newdata['api_result'] = "Error"
                #    newdata['api_error'] = str(e)                

                newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
                self.data.si2[f"stop_{stop}"] = newdata
                
            for line in ','.join(set(si2data["lines"].split(','))).split(','):
                newdata = self.data.si2[f"line_{line}"]
                #TODO: CHECK FOR FRESHNESS TO NOT KILL OFF THE KEYS

                #try
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
                #except Exception as e:
                #    newdata['api_result'] = "Error"
                #    newdata['api_error'] = str(e)                

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
                rightnow = now(self.hass.config.time_zone)
                min = int(s[0]) * 60 + int(s[1]) - (rightnow.hour * 60 +
                                                    rightnow.minute)
                if min < 0:
                    min = min + 1440
                return min
        except Exception:
            ##TODO LOG EXCEPTION
            return
        return
        
    async def process_ri4(self, notarealarg=None):

        iconswitcher = {
            'Buses': 'mdi:bus',
            'Trams': 'mdi:tram',
            'Ships': 'mdi:ferry',
            'Metros': 'mdi:subway-variant',
            'Trains': 'mdi:train',
        }

        for ri4key in self.data.ri4keys:
            ri4data = self.data.ri4keys[ri4key]
            api = slapi_ri4(ri4key, 60)
            for stop in ','.join(set(ri4data["stops"].split(','))).split(','):
                newdata = self.data.ri4[stop]
                #TODO: CHECK FOR FRESHNESS TO NOT KILL OFF THE KEYS
                
                #try:
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
                #except Exception as e:
                #    newdata['api_result'] = "Error"
                #    newdata['api_error'] = str(e)
                
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
        
        for tl2key in self.data.tl2:
            
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

            #try:         
        
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
            #except Exception as e:
            #    newdata['api_result'] = "Error"
            #   newdata['api_error'] = str(e)
            dispatcher_send(self.hass, "tl2_data_update")
            
            newdata['api_lastrun'] = now().strftime('%Y-%m-%d %H:%M:%S')
            self.data.tl2[tl2key] = newdata
            
        return


    async def prosess_queue(self, notarealarg=None):
        """Recuring tasks for installed repositories."""
        if not self.queue.has_pending_tasks:
            self.logger.debug("Nothing in the queue")
            return
        if self.queue.running:
            self.logger.debug("Queue is already running")
            return

        self.system.status.background_task = True
        self.hass.bus.async_fire("hasl/status", {})
        
        #TODO
        #Background task should be performed here
        #Use queue if needed

        self.system.status.background_task = False
        self.hass.bus.async_fire("hasl/status", {})

