Home Assistant SL Integration (HASL)
======================================

This is an integration that provides multiple sensors for Stockholms Lokaltrafik in Stockholm, Sweden. It provides intelligent sensors for Departures, Deviations, Vehicle Locations and Traffic Status. It also provides services for Location ID lookup and Trip Planing.

The integration should be pretty self explanatory but if you need assistance please find documentation at https://hasl.sorlov.com

## Install using HACS

First, visit [https://www.trafiklab.se/api](https://www.trafiklab.se/api) and create a free account. They provide multiple APIs, the ones you want are ["SL Trafikinformation 4"](https://www.trafiklab.se/api/sl-realtidsinformation-4) and ["SL Störningsinformation 2"](https://www.trafiklab.se/api/sl-storningsinformation-2), optionally you can also register for ["SL Trafikläget 2"](https://www.trafiklab.se/api/sl-trafiklaget-2) to get status sensors. When you have your API keys, you're ready to add the component to your Home Assistant.

## Visualisation

The sensors should be able to be used multiple cards in hasl-cards ([departure-card](https://github.com/hasl-platform/lovelace-hasl-departure-card), [traffic-status-card](https://github.com/hasl-platform/lovelace-hasl-traffic-status-card)) . There are several cards for different sensors and presentation options for each sensor type.

![card](https://user-images.githubusercontent.com/8133650/56198334-0a150f00-603b-11e9-9e93-92be212d7f7b.PNG)

