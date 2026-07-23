# Changelog

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
