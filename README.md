SL sensor for Home Assistant
========================

This is a simple component for Home Assistant that can be used to create a "Departure board" for buses and trains in Stockholm, Sweden.  You have to install it as a custom component and you need to get your own API key from SL / Trafiklab.

- First, visit [https://www.trafiklab.se/api](https://www.trafiklab.se/api) and create a free account. They provide multiple APIs, the one you want is ["SL Trafikinformation 4"](https://www.trafiklab.se/api/sl-realtidsinformation-4).  
When you have your API key, you're ready to add the component to your Home Assistant. Since this is a custom component, you need to add it manually to your config directory.

- Create a folder named **custom_components** under your Home Assistant **config** folder. 

- Create a folder named **sensor** under the **custom_components** folder.

- Download sl.py from here and put it in the **sensor** folder.

- Edit your configuration.yaml file and add the component

```yaml
# Example configuration.yaml entry
- platform: sl
  name: gullmarsplan
  ri4key: YOUR-API-KEY-HERE
  siteid: 9189
  lines: 17, 18, 19
  direction: 1
```


**Configuration variables**


- name: The name of the sensor (will be prefixed with "sl_") 

- ri4key: Your API key from Trafiklab

- siteid: The ID of the bus stop or station you want to monitor.  You can find the ID with some help from another API, **sl-platsuppslag**.  In the example above, site 9189 is Gullmarsplan.

- lines: (optional) A comma separated list of line numbers that you are interested in. Most likely, you only want info on the bus that you usually ride.  If omitted, all lines at the specified site id will be included.  In the example above, lines 17, 18 and 19 will be included.

- direction: (optional) Unless your site id happens to be the end of the line, buses and trains goes in both directions.  You can enter **1** or **2**.  If omitted, both directions are included. 

**sensor value**

The sensor value is the number of minutes to the next departure.  There are also a number of attributes:

```
next_departure: 1 min
next_line: 17
next_destination: Åkeshov
upcoming_departure: 4 min
upcoming_line: 18
upcoming_destination: Hässelby strand
unit_of_measurement: min
icon: fa-subway
friendly_name: sl gullmarsplan
attribution: Data from sl.se / trafiklab.se
```
