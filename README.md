# SweTrack for Home Assistant

Unofficial Home Assistant custom integration for SweTrack GPS trackers.

> Early development version. The API field mapping must be verified against
> real SweTrack Lite+ payloads before this should be treated as production-ready.

## Current features

- GUI setup using a SweTrack external API key
- Automatic discovery of all trackers returned by the account
- One Home Assistant device per tracker
- GPS device tracker
- Battery, external voltage, speed and last-seen sensors
- Online, ignition and external-power binary sensors
- Options flow for enabling/disabling trackers
- Automatic or fixed polling interval
- Automatic interval calculation when API quota headers/data are available
- Reauthentication and redacted diagnostics
- Norwegian and English translations

## Installation with HACS custom repository

1. Create a new public GitHub repository, for example `ha-swetrack`.
2. Upload **all files from this project root**, preserving the folder structure.
3. Replace `YOUR_GITHUB_USERNAME` in
   `custom_components/swetrack/manifest.json`.
4. In GitHub, create a release/tag such as `v0.1.0`.
5. In Home Assistant, open HACS → Integrations.
6. Open the menu → Custom repositories.
7. Paste the GitHub repository URL and select category **Integration**.
8. Find SweTrack in HACS and install it.
9. Restart Home Assistant.
10. Go to Settings → Devices & services → Add integration → SweTrack.

## Manual installation

Copy:

```text
custom_components/swetrack
```

to:

```text
/config/custom_components/swetrack
```

Restart Home Assistant and add SweTrack from the Integrations page.

## API key

The public API uses a Bearer API key. The integration does not store or use
your SweTrack username/password.

## First hardware test

After setup, download diagnostics from the SweTrack integration and inspect it
before sharing. Diagnostics redact common credentials, IMEI/serial fields and
coordinates, but always verify the file manually.

Useful logs:

```yaml
logger:
  default: info
  logs:
    custom_components.swetrack: debug
```

## Known limitations in v0.1.0

- Real Lite+ Gen1/Gen2 payloads have not yet been captured.
- Some field names may need adjustment.
- New trackers discovered after setup may require reloading the integration.
- Tracker filtering currently reloads the integration.
- Account-level API quota sensors are planned, but quota data is already
  included in diagnostics.
