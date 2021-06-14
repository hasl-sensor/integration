# ha-sensor-sl

Changelog for HomeAssistant SL Sensor (HASLv3).

The format is based on [Keep a Changelog][keep-a-changelog]
<!-- and this project adheres to [Semantic Versioning][semantic-versioning]. -->

## [3.0.0-beta.2] (2021-06-14)

### Fixes
- [#7](https://github.com/hasl-sensor/integration/issues/7) fixed. Too many programming languages I guess... =)
- [#6](https://github.com/hasl-sensor/integration/issues/6) fixed. Fault management implemented.
- Fixed double type datetime.datetime vs datetime in haslworker

## [3.0.0-beta.1] (2021-06-11)

Generally stuff could be really broken right now and I'm working on lots of stuff all over the code.
Forked from 2.2.3 but changes from later versions are implemented as needed.

### Changed (summarized)
- Moving into the new organization on github and renaming to integration
- Changed domain from hasl to hasl3
- Removed dependency on external hasl-communication-library and replaced by internal slapi dependency instead
- Using httpx async in slapi library
- Added GUI configuration for the integration
- Metadata added to the home assistant wheels repo, PR [#48](https://github.com/home-assistant/wheels-custom-integrations/pull/48) and [#57](https://github.com/home-assistant/wheels-custom-integrations/pull/57)
- Icons added to the home assistant brands repo, PR [#1606](https://github.com/home-assistant/brands/pull/1606) and [#1626](https://github.com/home-assistant/brands/pull/1626)
- Changed the unique naming of all enteties generated to be truly unique and stay the same over time
- Allow use of multiple API-keys for different sensors using multiple integrations
- Enforce time based caching between all integrations to reduce wear on the API-keys
- Workers to handle updates etc are now run on one minute intervalls using call-backs to be friendlier on hass
- Sensors are "just" retreiving data from the workers data instead of directly interfacing the apis.
- Devices are now created for each integration to be used for future automation etc
- Departures entity is now providing Deviation data only if a Deviation integration is configured with the same stops/lines to decrease complexity but maintaining compability both with new and old architechture.
- Deviation sensors are now availiable as separate entites/sensors if needed and are leveraged by the Departures sensors if they exist.
- A common in-memory structure for all data is now done using a worker holding data for all instances instead of writing to disk
- Updated hacs.json and info.md to be updated for v3
- Service for dumping the cache to disk have been implemented
- Fixed lots of bugs related to data not beeing available yet (async issues)
- Generic extensible queing system built in
- Services for location lookup and trip planning implemented
- Traffic status now is one sensor per traffic type to make it simpler to display status
- All sensortypes works and returns some kind of data if configured with valid data
- Added dependency on jsonpickle as the builtin json serialiser kind of sucks
- Added version field to manifest
- Added system health checks
- Services now response on the event bus by hasl3_response
- Services can be called via the event bus on hasl3_execute with argument cmd=<service> and then the rest of the argument as when normally using when calling a service
- Binary sensor logging and fault management implemented
- Slapi and haslworker logging and fault management implemented
- Sensor logging and fault management implemented
- Changed fork from DSorlov to hasl-sensor

## [2.2.7] (2021-06-08)

### Changed
- Workaround fix for timezone error

## [2.2.6] (2021-05-18)

### Changed
- Fixed version numbers discrepencies

## [2.2.5] (2021-05-10)

### Changed
- Updated manifest.json

## [2.2.4] (2020-05-23)

### Changed
- Documentation updates

## [2.2.3] (2020-03-04)

### Changed
- Bugfixes

## [2.2.2] (2020-03-01)

### Changed
- Release with right branch

## [2.2.1] (2020-03-01)

### Changed
- PR [#44](https://github.com/DSorlov/hasl-platform/pull/44) [#49](https://github.com/DSorlov/hasl-platform/pull/49) Fixed bug where no departures were returned if no lines specified [@Ziqqo](https://github.com/Ziqqo) [@lindell](https://github.com/lindell)
- PR [#49](https://github.com/DSorlov/hasl-platform/pull/49) Minutes from expected time [@lindell](https://github.com/lindell)
- Updated HACS configuration

## [2.2.0] (2019-07-18)

### BREAKING CHANGES
- config entrys have been changed to a true string array and should now be specified according to `lines: ['123X','124']`

### Changed
- Fix [#36](https://github.com/DSorlov/hasl-platform/issues/36) platform not found
- Fix [#37](https://github.com/DSorlov/hasl-platform/issues/37) lines in 2.1.3
- Moved the cache file from config dir into the .storage folder
- Fixed documentation error (said TI2KEY instead of TL2KEY)

### Added
- Added services Platsupplslag and Reseplaneraren as services (preview, no docs yet)

## [2.1.3] (2019-07-15)

### Changed
- Replaced custom updater with [HACS](https://custom-components.github.io/hacs/)

## [2.1.2] (2019-07-15)

### Changed
- Replaced custom updater with [HACS](https://custom-components.github.io/hacs/)
- Minor changed in documentation
- Fixed bad custom_updater.json file

## [2.1.1] (2019-06-04)

### Changed
- Fix [#32](https://github.com/DSorlov/hasl-platform/issues/32) error management fails
- Fix [#27](https://github.com/DSorlov/hasl-platform/issues/27) implemented filtering on "lines" for departure sensors

## [2.1.0] (2019-05-21)

### BREAKING CHANGES
- `comb` sensor is now `departures`, will remove `comb` in 2.5.0. Please change your config.
- `tl2` sensor is now `status`, will remove `tl2` in 2.5.0. Please change your config.

### Changed
- Fix [#23](https://github.com/DSorlov/ha-sensor-sl/issues/23) timewindow not working
- Fix [#24](https://github.com/DSorlov/ha-sensor-sl/issues/24) default scan_interval documentation bug
- Fix [#25](https://github.com/DSorlov/ha-sensor-sl/issues/25) stupid bug introduced by DSorlov =)
- PEP8 Compliance
- Branched all display cards to new project [hasl-cards](https://github.com/DSorlov/hasl-cards).
- Renamed repository from ha-sensor-sl to hasl-platform to conform to new naming.
- Updated massive amounts of links and documentation
- Many stability improvements and minor bugfixes

### Added
- Implemented basic error handling as exceptions are now raised from communications library.
- Implemented new sensor based on real-time train location api (EXPERIMENTAL!)

## [2.0.2] (2019-04-30)

### Changed
- Fixed [#19](https://github.com/DSorlov/ha-sensor-sl/issues/19) Small changes for custom_updater

## [2.0.1] (2019-04-30)

### Changed
- Fixed [#18](https://github.com/DSorlov/ha-sensor-sl/issues/18) missing indentation in sensor.py

## [2.0.0] (2019-04-30)

### BREAKING CHANGES
- Changed structure in configuration to be more standarlized, avoid key duplication etc
- Cannot be used pre 0.92 as dependency code has moved (or atleast I have not tried it)
- New install location for the autoupdater (changed from folder sl to hasl)
- Rename of sl-card.js to hasl-comb-card.js

### Changed
- Changed naming of a few functions to make it more clean
- Fixed issue #16: sync_interval not working
- Fixed issue #11: wrong time shown, thanks to [@isabellaalstrom] for suggesting fix
- Language is now picked from config first, then from browser, and then default sv-SE
- Icon changed to mdi:bus if no deviances, otherwise mdi:bus-alert
- Recomended install directory is now 'hasl' instead of 'sl' to align naming
- Fixed the autoupdater URLS (dev branch will be off but who cares, dev should not be used in prod)
- Using HASL 2.0.0 Communications Library with support for Trafikläget2 API from SL
- Implemented a request minimization strategy for API-calls / using caching (haslcache.json) when using multiple sensors for same stops

### Added
- Config 'property' in comb sensor to set which property that is reported as default state
- Config 'always_show_time' in hasl-comb-card.js to force also showing time when less than 60 minutes to departure when 'timeleft' is set
- Added __init.py__ and manifest.json to support 0.92+ version of home assistant, thanks to [@dimmanramone] 
- Added property deviation_count to comb sensor to show number of deviations in total
- New sensor type TL2 for displaying trafic status messages for the Trafikläget2 API
- Service for force clearing of cache (adds services.json, mostly for troubleshooting)

## [1.0.3] (2019-04-16)

### Changed
- Missing default value for direction parameter
- Integrated magic to better show time left to departure from fork [lokanx-home-assistant](https://github.com/lokanx-home-assistant/ha-sensor-sl/commit/df7de55f040a7fab5b15be176ec5d61400b1dbba)
- Added support for languages (sv-SE and en-EN) in sl-card.js

## [1.0.2] (2019-04-16)

### Changed
- Fix for naming of unique_id for certain cases (still not good however)
- sl-card.js enhanced and styled by [@dimmanramone](https://github.com/dimmanramone)! Huge thanks!!

## [1.0.1] (2019-04-15)

### Changed
- Fixed documtentation about interval being changed to scan_interval this to better support the Home Assistant standard.
- Fixed direction parameter that had been hardcoded for some strage reason. Blaming it on someone else. =)

## [1.0.0] (2019-04-12)

### Added
- Added configuration for TimeWindow
- Added friendly_name (and removed name)
- Updated sl-card.js to support time or minutes departures
- Exposed unique_id for each sensor
- Added multiple properties to the sensor output

### Changed
- Moved communication to external PyPi library (HASL)
- Changed default repo from dev to hasl
- Cleaned up the code
- Using constant keywords from HomeAssistant
- If update error occures now deliver '-' as value instead of -1

### Removed
- name configuration (replaced by friendly_name)

## [0.0.8] (2019-04-11)

### Changed
- Moved /sensor/sl.py to /sl/sensor.py
- Fixed bad formatting of custom_updater files
- Fixed custom_updater instructions in readme
- Fixed broken encoding issues for rendering in sl-card.js

## [0.0.7] (2018-12-13)

### Added
- Rendering of deviances
- Parameters to customize card

### Changed
- Rendering strategy

## [0.0.6] (2018-11-16)

### Added
- Added output of icons

### Changed
- Buggfixes in lookup
- Changed rendering in lovelace card

## [0.0.5] (2018-11-16)

### Added
- Dependency for new https://www.trafiklab.se/api/sl-storningsinformation-2
- Lovelace card

### Changed
- Logging strings changed to indicate which api failed
- User Agent String conforms to standard
- Now renders the next hour of departures

### Removed
- JavaScript output

## [0.0.4] (2018-09-30)

### Added
- Use a binary_sensor to enable/disable API-calls
- Log error code and message once in case of error at API call
- Support for custom_updater

### Changed
- Log error message instead of just reporting failure.
- Changed fork from fredrikbaberg to DSorlov

## [0.0.3] (2018-09-30)

### Changed
- Only log errors once

## [0.0.2] (2018-09-29)

### Changed
- Log error code.
- Changed fork from fuffenz to fredrikbaberg

## [0.0.1] (2018-05-08)

### Initial release
- This is a great day indeed.

[keep-a-changelog]: http://keepachangelog.com/en/1.0.0/
[3.0.0-beta.2]: https://github.com/hasl-sensor/integration/compare/3.0.0-beta.1...3.0.0-beta.2
[3.0.0-beta.1]: https://github.com/hasl-sensor/integration/compare/3.0.0-beta.1...DSorlov:2.2.7
[2.2.7]: https://github.com/DSorlov/hasl-platform/compare/2.2.6...2.2.7
[2.2.6]: https://github.com/DSorlov/hasl-platform/compare/2.2.5...2.2.6
[2.2.5]: https://github.com/DSorlov/hasl-platform/compare/2.2.4...2.2.5
[2.2.4]: https://github.com/DSorlov/hasl-platform/compare/2.2.3...2.2.4
[2.2.3]: https://github.com/DSorlov/hasl-platform/compare/2.2.3...2.2.2
[2.2.2]: https://github.com/DSorlov/hasl-platform/compare/2.2.2...2.2.1
[2.2.1]: https://github.com/DSorlov/hasl-platform/compare/2.2.1...2.2.0
[2.2.0]: https://github.com/DSorlov/hasl-platform/compare/2.2.0...2.1.3
[2.1.3]: https://github.com/DSorlov/hasl-platform/compare/2.1.3...2.1.2
[2.1.2]: https://github.com/DSorlov/hasl-platform/compare/2.1.1...2.1.2
[2.1.1]: https://github.com/DSorlov/hasl-platform/compare/2.1.0...2.1.1
[2.1.0]: https://github.com/DSorlov/hasl-platform/compare/2.0.3...2.1.0
[2.0.3]: https://github.com/DSorlov/hasl-platform/compare/2.0.2...2.0.3
[2.0.2]: https://github.com/DSorlov/hasl-platform/compare/2.0.1...2.0.2
[2.0.1]: https://github.com/DSorlov/hasl-platform/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/DSorlov/hasl-platform/compare/1.0.3...2.0.0
[1.0.3]: https://github.com/DSorlov/hasl-platform/compare/1.0.2...1.0.3
[1.0.2]: https://github.com/DSorlov/hasl-platform/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/DSorlov/hasl-platform/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/DSorlov/hasl-platform/compare/0.0.8...1.0.0
[0.0.8]: https://github.com/DSorlov/hasl-platform/compare/0.0.7...0.0.8
[0.0.7]: https://github.com/DSorlov/hasl-platform/compare/0.0.6...0.0.7
[0.0.6]: https://github.com/DSorlov/hasl-platform/compare/0.0.5...0.0.6
[0.0.5]: https://github.com/DSorlov/hasl-platform/compare/v0.0.4...0.0.5
[0.0.4]: https://github.com/fredrikbaberg/ha-sensor-sl/compare/v0.0.3...DSorlov:v0.0.4
[0.0.3]: https://github.com/fredrikbaberg/ha-sensor-sl/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/fredrikbaberg/ha-sensor-sl/compare/fredrikbaberg:v0.0.2...fuffenz:master
[0.0.1]: https://github.com/fuffenz/ha-sensor-sl