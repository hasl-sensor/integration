![maintained](https://img.shields.io/maintenance/yes/2021.svg)
[![hacs_badge](https://img.shields.io/badge/hacs-default-green.svg)](https://github.com/custom-components/hacs)
[![ha_version](https://img.shields.io/badge/home%20assistant-0.98%2B-green.svg)](https://www.home-assistant.io)
![version](https://img.shields.io/badge/version-3.0.0_beta.1-lightgrey.svg)
![stability-alpha](https://img.shields.io/badge/stability-beta-lightgrey.svg)
[![maintainer](https://img.shields.io/badge/maintainer-dsorlov-blue.svg)](https://github.com/DSorlov)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Home Assistant SL Integration (HASLv3)
======================================

This is a integration to provide multiple sensors for Stockholms Lokaltrafik in Stockholms Län, Sweden. It provides intelligent sensors for departures, deviations, vehicle locations, traffic status and route monitoring. It also provides services for Location ID lookup and Trip Planing. You will still need to get your own API keys from SL / Trafiklab (se docs for [HASL](https://hasl.sorlov.com)).

This integration is prepared for the new API that will be released from SL during 2021 (preliminary date). The legacy version (HASL) will NOT be upgraded once this happens.

Documentation is available for HASL at http://hasl.sorlov.com, for HASLv3 it will be available once done at the same location, until then this page serves as documentation.

## Install using HACS

First, visit [https://www.trafiklab.se/api](https://www.trafiklab.se/api) and create a free account. They provide multiple APIs, the ones you want are ["SL Trafikinformation 4"](https://www.trafiklab.se/api/sl-realtidsinformation-4) and ["SL Störningsinformation 2"](https://www.trafiklab.se/api/sl-storningsinformation-2), optionally you can also register for ["SL Trafikläget 2"](https://www.trafiklab.se/api/sl-trafiklaget-2) to get status sensors. When you have your API keys, you're ready to add the component to your Home Assistant.

Then go into HACS and search for HASLv3 under the Integrations headline (HASL is the legacy version, see below).

You will need to restart Home Assistant to finish the process. Once that is done reload your GUI (caching issues preventing the integration to be shown).

Goto Integrations and add HASLv3

## Manual installation (not advised)

The integration can be installed manually by copying some files from this repo to your install. Also you will need to create API key and config as outlined in the previous section.
Note that HASLv3 will not automatically update as newer versions are released so you need to keep track of that yourself. We recomend using HACSv3 as outlined above in the previous section.

Please copy all files fron the `custom_components\hasl3` files into the `<config>/custom_components/hasl3/` directory. You need to restart Home Assistant and reload the GUI to make sure the integration is available.Goto Integrations and add HASLv3.

where `<config>` is your Home Assistant configuration directory.

## Legacy version will soon die but not yet..

HASL is still available from https://github.com/DSorlov/hasl-platform and will be for some time to support those who are afraid of progressing and learning new things and for those who prefer the old yaml configuration method and the old sensor architechture. Or atleast to the planned SL API-changes are made. Then it will die.

## Visualisation

None of the existing lovelace cards have been tested with HASLv3. It will be updated as soon as time permits.

The sensors should be able to be used multiple cards in hasl-cards ([departure-card](https://github.com/hasl-platform/lovelace-hasl-departure-card), [traffic-status-card](https://github.com/hasl-platform/lovelace-hasl-traffic-status-card)) . There are several cards for different sensors and presentation options for each sensor type.

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)

## Sensors

One objective during rewrite have been to not touch the existing sensors so much to make sure it is compatible as far as possible. This table also contains differances between v2.x (Legacy) and HASLv3.

| HASL | HASLv3 | Sensor Name | Description | Notes |
| -- | -- | -- | -- | -- |
| :heavy_check_mark: | :heavy_check_mark: | Departures | Departure information for a given SL Hållplats | Same between both versions. In v3 Deviation Sensor is used for deviation information. |
| :x: | :heavy_check_mark: | Deviations | Is there any changes in traffic?  | This was available in v2 as a integrated data in Departures, now supports both locations and lines to be able to build panels etc. |
| :x: | :heavy_check_mark: | Route | Current best route between A and B | Looks up a current route between point A and B. Takes current traffic and deviations into account. |
| :heavy_check_mark: | :heavy_check_mark: | Traffic Status | High level status for different traffic types | In v2 one combined sensor is created for all traffic types while in v3 a binary_sensor is created for each selected type. |
| :heavy_check_mark:* | :heavy_check_mark: | Vehicle Locations | How many vehicles and their locations | Was experimental in v2 and data is cleaned up in v3. A separate sensor is created for each type of traffic |

## Services and events

HASLv3 implements some services that can be useful for accessing data and using for automations or whatnot. Anyway. There are five services that can be used. They return data by triggering an event on the `hasl3_response` topic.

- `dump_cache` No arguments. Dumps the cache to a file in the Home Assistant configuration directory. Returns the filename of the created file in an event.
- `get_cache` No arguments. Returns the cache of the created file in an event.
- `find_location`: Arguments `api_key`, `search_string`. Returns the closest stop to the search string provided.
- `find_trip_id` Arguments `api_key`, `org`, `dest`. Returns a trip from org to dest.
- `find_trip_pos` Arguments `api_key`, `orig_lat`, `orig_long`, `dest_lat`, `dest_long`. Returns a trip from org to dest.

## Debugging and logging

HASLv3 is using the standard logging facilities in Home Assistant. There is some logging of normal operations but it have been built to be as quiet as possible. Keys and APIs will mostly just log a failure to debug and retry next time. Such things do occur from time to time due to API or just Internet. However setup and other more defining actions are logged as errors to make sure you see them. However you can tweak logging:

````
logger:
  logs:
    custom_components.hasl3.core: debug       # Plattform setup and startup
    custom_components.hasl3.config: debug     # Booring.. this is setup stuff when creating sensors
    custom_components.hasl3.sensor: debug     # Mostly booring startup and keying stuff, can be needed
    custom_components.hasl3.services: debug   # Can be needed if you use services/events
    custom_components.hasl3.worker: debug     # This is the communications coordinator, can be needed
    custom_components.hasl3.slapi: debug      # This is SLAPI, the underlying library, should be needed
````

## Stuff I am thinking about implementing or refining

- Input validation missing for creating new integration, field syntax validation is already done by HA but perhaps key validation or similar could be peformed?
- Input validation missing for setting integration options, field syntax validation is already done by HA but perhaps key validation or similar could be peformed?

## API-call restrictions and optimizations

The `Bronze` level API is limited to 30 API calls per minute, 10.000 per month. With 10.000 calls per month, that allows for less than one call every 4 minute but if you are using multiple sensors this is split between them and each config sensor section can contain a separate pair of api-keys.
The calls have been optimized and are beeing locally cached for the specified freshness, if multiple sensors are using the same siteid there will still only be one call. Caching is done in a file (haslcache.json) that will be automatically created in the configuration directory.
You can also specify a binary_sensor that perhaps is turned of when no-one is at home or similar to reduce the number of calls. Optimizations can be turned of if needed in very specific situation or if you have a high level API-key.
