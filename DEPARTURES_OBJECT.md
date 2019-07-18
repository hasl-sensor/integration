SL Departures Sensor Object
===============================

The sensor value is the number of minutes to the next departure (or if something else is configured that will be used instead).
There are also a large number of attributes that can help you with filtering or whatever you need:

```
friendly_name: Mölnvik
unit_of_measurement: min
icon: mdi:subway
attribution: Stockholms Lokaltrafik
last_refresh: 2018-11-16 19:08:40
next_departure_minutes: 10
next_departure_time: 19:18:40
deviation_count: 1
refresh_enabled: on
departures: [{
  line: 474
  direction: 1
  departure: 10 min
  destination: Slussen
  diff: 10
  type: Buses
  groupofline: blåbuss
  icon: mdi:bus
}]
deviances: [{
  updated: 2018-11-16T15:59:40.063+01:00
  title: Inställd avgång
  fromDate: 2018-11-16T15:59:40.663
  toDate: 2018-11-17T00:00:00
  details: "Mölnvik kl 16:17 till Slussen är inställd pga framkomlighetsproblem - köer."
  sortOrder: 1
}]
```