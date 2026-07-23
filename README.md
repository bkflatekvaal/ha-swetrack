<p align="center">
  <img src="logo.svg" width="140" alt="SweTrack">
</p>

# SweTrack for Home Assistant

Unofficial Home Assistant integration for SweTrack GPS trackers.

## Features

- GUI setup using a SweTrack external API key
- Multiple SweTrack accounts/config entries
- One parent **SweTrack API** device per config entry
- Trackers shown as connected devices below their API account
- GPS device tracker
- Battery, external voltage, speed, speed limit and last-seen sensors
- Online, ignition, external-power, power-saving and relay status
- API quota and polling diagnostics
- Automatic or fixed polling interval
- Options flow for enabling/disabling trackers
- Reauthentication and privacy-preserving diagnostics
- Local Home Assistant/HACS brand assets
- Norwegian and English translations

## Installation with HACS custom repository

1. Open HACS → Integrations.
2. Open the menu → Custom repositories.
3. Add:
   `https://github.com/bkflatekvaal/ha-swetrack`
4. Select category **Integration**.
5. Install SweTrack.
6. Restart Home Assistant.
7. Go to Settings → Devices & services → Add integration → SweTrack.

## API key

The integration uses a SweTrack Bearer API key. It does not require or store
your SweTrack username/password.

## Device hierarchy

Each config entry creates one parent API device:

```text
SweTrack API – account
├── Tracker 1
├── Tracker 2
└── Tracker 3
```

Adding another API key as a separate config entry creates another independent
API parent device.

## Diagnostics and privacy

Diagnostics redact API credentials, cookies, account/tracker names, device
identifiers, IMEI/unique IDs, groups and GPS coordinates. Always review a
diagnostics file before publishing it publicly.

## Debug logging

```yaml
logger:
  default: info
  logs:
    custom_components.swetrack: debug
```

## Version 0.2.1

- Added parent API device and `via_device` tracker relationships
- Added multiple config-entry support
- Added API usage sensors
- Added local brand assets supplied by the repository owner
- Added entity icons and model generation detection
- Refreshed documentation
- Added repository-level HACS brand assets
- Read account username from `/account/info`
- Changed device configuration link to SweTrack Live


## Data updates

Version 0.2.1 uses REST polling through `/devices/info`. It does not register a
webhook. SweTrack webhooks may be considered later as an optional mode for
accounts where SweTrack support has enabled push delivery and Home Assistant
has a securely reachable external URL.
