"""Diagnostics privacy regression tests runnable without Home Assistant."""

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


class DiagnosticsTests(unittest.IsolatedAsyncioTestCase):
    async def test_account_ids_are_redacted_from_diagnostics(self):
        prefix = "swetrack_diagnostics_test"
        package = ModuleType(prefix)
        package.__path__ = []
        const = ModuleType(f"{prefix}.const")
        const.DOMAIN = "swetrack"
        config_entries = ModuleType("homeassistant.config_entries")
        config_entries.ConfigEntry = SimpleNamespace
        core = ModuleType("homeassistant.core")
        core.HomeAssistant = SimpleNamespace
        modules = {
            prefix: package,
            f"{prefix}.const": const,
            "homeassistant": ModuleType("homeassistant"),
            "homeassistant.config_entries": config_entries,
            "homeassistant.core": core,
        }
        path = (
            Path(__file__).resolve().parents[1]
            / "custom_components/swetrack/diagnostics.py"
        )
        spec = importlib.util.spec_from_file_location(f"{prefix}.diagnostics", path)
        diagnostics = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(diagnostics)

        entry = SimpleNamespace(
            entry_id="test-entry",
            data={"account_id": "private-account", "api_key": "private-key"},
            options={},
        )
        payload = {"accounts": [{"account_id": "private-account", "status": "ok"}]}
        coordinator = SimpleNamespace(
            last_update_success=True,
            update_interval=None,
            request_limit=100,
            request_count=1,
            requests_remaining=99,
            reset_at=None,
            device_count=1,
            last_headers={},
            last_raw_payload=payload,
        )
        hass = SimpleNamespace(data={"swetrack": {entry.entry_id: coordinator}})

        result = await diagnostics.async_get_config_entry_diagnostics(hass, entry)

        self.assertEqual(result["entry"]["data"]["account_id"], "**REDACTED**")
        self.assertEqual(result["entry"]["data"]["api_key"], "**REDACTED**")
        self.assertEqual(
            result["coordinator"]["payload"]["accounts"],
            [{"account_id": "**REDACTED**", "status": "ok"}],
        )
        self.assertEqual(result["coordinator"]["requests_remaining"], 99)
        self.assertEqual(entry.data["account_id"], "private-account")
        self.assertEqual(payload["accounts"][0]["account_id"], "private-account")
