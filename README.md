<p align="center">
  <img src="https://raw.githubusercontent.com/bkflatekvaal/ha-swetrack/main/logo.png" width="140" alt="SweTrack">
</p>

# SweTrack for Home Assistant

Follow your SweTrack GPS trackers in Home Assistant. This unofficial integration
supports multiple accounts and is available in English and Norwegian Bokmål.

Requires Home Assistant 2026.8 or newer and a SweTrack external API key.

## Features

- Show tracker locations on the map.
- Monitor battery, speed, last seen, and connection status.
- View additional readings, such as ignition, external power, temperature, and
  humidity, when supported by your tracker.
- Keep track of API usage and choose automatic or fixed update intervals.

Available sensors depend on the tracker model and the data SweTrack provides.

## Installation

### Marketplace (Home Assistant 2026.11+)

Marketplace replaces HACS in Home Assistant 2026.11.

1. Open **Settings > Marketplace** as an administrator.
2. Select **Add from link** and connect GitHub if prompted.
3. Enter `https://github.com/bkflatekvaal/ha-swetrack` and select **Add**.
4. Open **SweTrack** and select **Install**. If asked for a type, select **Integration**.
5. Follow the setup prompt and restart Home Assistant if requested.

If you already installed SweTrack through HACS, it moves to Marketplace when you
upgrade Home Assistant. You do not need to reinstall it.

### HACS (Home Assistant 2026.8–2026.10)

In HACS, open **Custom repositories** from the menu. Add
`https://github.com/bkflatekvaal/ha-swetrack` with type **Integration**, install
SweTrack, and restart Home Assistant.

## Setup

1. Create an external API key in the SweTrack app or web portal.
2. In Home Assistant, open **Settings > Devices & services > Add integration**
   and select **SweTrack** if setup has not already opened.
3. Paste your API key and complete setup.

Your SweTrack username and password are not required. To add another account,
repeat setup with that account's API key. Trackers are grouped under their account.

## Settings and updates

Open SweTrack under **Settings > Devices & services** to choose which trackers
are enabled and adjust the update interval.

Automatic mode adjusts the interval based on the available API quota. Fixed mode
uses your chosen interval. Data is checked periodically, so location changes are
not instant.

If the daily API quota is exhausted, Home Assistant shows a Repairs notification.
The integration reduces its request frequency and retries automatically. If an
API key expires, follow the Home Assistant prompt to enter a replacement key for
the same account.

## Help

Report problems in [GitHub Issues](https://github.com/bkflatekvaal/ha-swetrack/issues).
Include your Home Assistant and integration versions and describe what happened.
Never share your API key. Review any diagnostic files before sharing them.

See the [changelog](CHANGELOG.md) for release notes.
