"""Constants for the SweTrack integration."""

from datetime import timedelta

DOMAIN = "swetrack"
PLATFORMS = ["device_tracker", "sensor", "binary_sensor"]

CONF_API_KEY = "api_key"
CONF_ACCOUNT_ID = "account_id"
CONF_ACCOUNT_NAME = "account_name"
CONF_ACCOUNT_LANGUAGE = "account_language"
CONF_UPDATE_MODE = "update_mode"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_ENABLED_DEVICES = "enabled_devices"

UPDATE_MODE_AUTO = "auto"
UPDATE_MODE_MANUAL = "manual"

DEFAULT_UPDATE_MODE = UPDATE_MODE_AUTO
DEFAULT_MANUAL_INTERVAL = 180
MIN_UPDATE_INTERVAL = 60
MAX_UPDATE_INTERVAL = 3600
DEFAULT_AUTO_INTERVAL = 180
AUTO_RESERVE_RATIO = 0.15
FALLBACK_INTERVAL = timedelta(minutes=3)

API_BASE_URL = "https://api.cloudappapi.com/publicapi/v1/"
API_DEVICES_INFO = "devices/info"
API_ACCOUNT_INFO = "account/info"

ATTRIBUTION = "Data provided by SweTrack"
