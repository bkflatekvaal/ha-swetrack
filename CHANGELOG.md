# Changelog

## 0.2.7

- Create tracker entities only when the capability is exposed by `/devices/info`
- Distinguish unsupported hardware from a supported sensor with a null/currently unavailable value
- Temperature and humidity are omitted on trackers without `temp_hum`
- Wake-up entities are created individually based on the keys exposed in `wakeup_info.current_settings`
- Ignition, relay, external power/voltage, speed and power-saving entities also respect API capability presence
- Automatically removes stale optional temperature/humidity/wake-up entities created by v0.2.6

## 0.2.6

- Renamed external power to `External power connected`
- Ensured ignition is displayed as `Ignition`, not generic `Power`
- Added temperature and humidity sensors with API value scaling
- Added wake-by-time, wake-by-vibration, wake-by-light and safety-zone diagnostics
- Added wake-up interval diagnostic sensor
- Added cached total event count, refreshed every 15 minutes
- Added explicit binary sensor fallback names

## 0.2.5

- Added robust automatic reauthentication for invalid or expired API keys
- Prevented a replacement key from switching the config entry to another account
- Refreshes account name and language during reauthentication
- Added a persistent Repairs issue when the daily API quota is exhausted
- Automatically removes the quota issue after successful communication
- Cleans up Repairs issues when the config entry is removed
- Improved first-time setup error handling for migrated config entries
- Corrected documentation and issue tracker URLs in the manifest

## 0.2.4

- Added local dark-mode icon and logo variants
- Changed README logo to an absolute raw GitHub PNG URL
- Added root `logo.png` for HACS README rendering
- Removed the unused repository-root `brand/` directory

## 0.2.3

- Added explicit entity names for all account diagnostic sensors
- Renamed quota reset timestamp to `Quota reset`
- Renamed tracker speed sensors to `Current speed` and `Speed limit`
- Added explicit fallback names to avoid generic device-name labels

## 0.2.2

- Shortened parent device name to `SweTrack – <account>`
- Renamed API diagnostic entities for clearer display
- Added tracker count and account language
- Kept all account sensors in the Diagnostic category

## 0.2.1

- Added repository-level `brand/` assets for HACS
- Correctly read `data.user.id`, `username`, `email` and `language`
- Improved parent API-device naming
- Changed configuration URL to `https://www.swetrack.com/live`
- Documented that the integration currently uses REST polling only

## 0.2.0

- Parent SweTrack API device per config entry
- Trackers linked through `via_device`
- Multiple API keys/config entries supported
- API daily limit, used, remaining, reset and polling sensors
- Local Home Assistant/HACS brand directory
- Improved entity icons
- Lite+ generation detection from model metadata

## 0.1.1

- Fixed Options Flow
- Added real API field mapping
- Improved diagnostic redaction

## 0.1.0

- Initial development release
