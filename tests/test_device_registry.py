"""Registry contract tests, runnable without Home Assistant on Windows.

Execute the real integration setup and entity code with a strict registry double.
These tests do not replace validation against a running Home Assistant registry.
"""

import ast
import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "swetrack"


class Registry:
    """Model scoped identity and accept only the registry parameters we use."""

    def __init__(self):
        self.entries = {}

    def async_get_or_create(
        self,
        *,
        config_entry_id,
        identifiers,
        manufacturer,
        model,
        name,
        configuration_url,
        via_device_id=None,
    ):
        key = (config_entry_id, frozenset(identifiers))
        if key not in self.entries:
            self.entries[key] = SimpleNamespace(id=uuid4().hex, name_by_user=None)
        device = self.entries[key]
        device.via_device_id = via_device_id
        device.identifiers = identifiers
        device.name = name
        return device


class CoordinatorEntity:
    def __class_getitem__(cls, item):
        return cls

    def __init__(self, coordinator):
        self.coordinator = coordinator


def module(name, **members):
    result = ModuleType(name)
    result.__dict__.update(members)
    return result


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


class DeviceRegistryTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.registry = Registry()
        self.hass = SimpleNamespace(
            data={},
            config_entries=SimpleNamespace(
                async_forward_entry_setups=AsyncMock(side_effect=self.forward),
                async_unload_platforms=AsyncMock(return_value=True),
            ),
        )
        self.forwarded = []
        self.coordinators = []

        def coordinator(hass, entry, api):
            result = SimpleNamespace(
                entry=entry,
                data={},
                async_config_entry_first_refresh=AsyncMock(),
            )
            self.coordinators.append(result)
            return result

        prefix = "custom_components.swetrack"
        stubs = {
            "homeassistant": module("homeassistant"),
            "homeassistant.config_entries": module(
                "config_entries", ConfigEntry=object
            ),
            "homeassistant.core": module("core", HomeAssistant=object),
            "homeassistant.exceptions": module(
                "exceptions",
                ConfigEntryAuthFailed=type("AuthFailed", (Exception,), {}),
                ConfigEntryNotReady=type("NotReady", (Exception,), {}),
            ),
            "homeassistant.helpers": module("helpers"),
            "homeassistant.helpers.device_registry": module(
                "device_registry",
                DeviceInfo=dict,
                async_get=lambda hass: self.registry,
            ),
            "homeassistant.helpers.issue_registry": module("issue_registry"),
            "homeassistant.helpers.aiohttp_client": module(
                "aiohttp_client",
                async_get_clientsession=Mock(),
            ),
            "homeassistant.helpers.update_coordinator": module(
                "update_coordinator",
                CoordinatorEntity=CoordinatorEntity,
            ),
            f"{prefix}.api": module(
                "api",
                SweTrackApiClient=Mock(),
                SweTrackApiError=Exception,
                SweTrackAuthError=Exception,
            ),
            f"{prefix}.coordinator": module(
                "coordinator",
                SweTrackCoordinator=coordinator,
            ),
            f"{prefix}.models": module("models", derive_account_identity=Mock()),
        }
        for name, stub in stubs.items():
            stub.__name__ = name
            stub.__path__ = []
        stubs["homeassistant.helpers"].device_registry = stubs[
            "homeassistant.helpers.device_registry"
        ]
        stubs["homeassistant.helpers"].issue_registry = stubs[
            "homeassistant.helpers.issue_registry"
        ]
        self.modules = patch.dict(sys.modules, stubs)
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.integration = load(prefix, COMPONENT / "__init__.py")
        self.entities = sys.modules[f"{prefix}.entity"]

    async def forward(self, entry, platforms):
        coordinator = self.hass.data["swetrack"][entry.entry_id]
        parent = self.registry.entries[
            (entry.entry_id, frozenset({("swetrack", f"account_{entry.entry_id}")}))
        ]
        self.assertEqual(coordinator.account_device_id, parent.id)
        self.assertEqual(platforms, ["device_tracker", "sensor", "binary_sensor"])
        self.forwarded.append(entry.entry_id)

    def entry(self, entry_id):
        return SimpleNamespace(
            entry_id=entry_id,
            title="Same account name",
            data={"account_id": entry_id, "api_key": "test-key"},
            async_on_unload=Mock(),
            add_update_listener=Mock(),
        )

    def tracker(self, entry, tracker_id):
        coordinator = self.hass.data["swetrack"][entry.entry_id]
        entity = self.entities.SweTrackEntity(coordinator, tracker_id)
        return self.registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **entity.device_info,
        )

    async def test_account_exists_before_platforms_even_without_trackers(self):
        entry = self.entry("first")
        self.assertTrue(await self.integration.async_setup_entry(self.hass, entry))
        self.assertEqual(self.forwarded, ["first"])
        coordinator = self.coordinators[0]
        account_entity = self.entities.SweTrackAccountEntity(coordinator)
        parent = self.registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **account_entity.device_info,
        )
        self.assertEqual(parent.id, coordinator.account_device_id)
        self.assertEqual(len(self.registry.entries), 1)

    async def test_multiple_accounts_trackers_and_late_entities(self):
        first, second = self.entry("first"), self.entry("second")
        for entry in (first, second):
            await self.integration.async_setup_entry(self.hass, entry)
            for tracker_id in ("shared-serial", "another-serial"):
                child = self.tracker(entry, tracker_id)
                coordinator = self.hass.data["swetrack"][entry.entry_id]
                self.assertEqual(child.via_device_id, coordinator.account_device_id)
                self.assertEqual(child.identifiers, {("swetrack", tracker_id)})
                # A later capability entity must resolve to the same tracker device.
                self.assertEqual(self.tracker(entry, tracker_id).id, child.id)
        self.assertNotEqual(
            self.tracker(first, "shared-serial").via_device_id,
            self.tracker(second, "shared-serial").via_device_id,
        )

    async def test_existing_devices_reload_and_replacement_credentials(self):
        entry = self.entry("first")
        parent = self.registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            **self.entities.account_device_info(entry),
        )
        parent.name_by_user = "My account"
        child = self.registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("swetrack", "serial")},
            manufacturer="SweTrack",
            model=None,
            name="Old tracker",
            configuration_url="https://www.swetrack.com/live",
            via_device_id=parent.id,
        )
        child.name_by_user = "My tracker"
        for api_key in ("original", "replacement"):
            entry.data["api_key"] = api_key
            await self.integration.async_setup_entry(self.hass, entry)
            self.assertEqual(self.coordinators[-1].account_device_id, parent.id)
            self.assertEqual(self.tracker(entry, "serial").id, child.id)
            self.assertEqual(child.via_device_id, parent.id)
            self.assertTrue(await self.integration.async_unload_entry(self.hass, entry))
        self.assertEqual(parent.name_by_user, "My account")
        self.assertEqual(child.name_by_user, "My tracker")

    def test_no_deprecated_parent_keyword_or_lookup_in_integration(self):
        deprecated_keyword = "via_device"
        for path in COMPONENT.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.keyword):
                    self.assertNotEqual(node.arg, deprecated_keyword, path)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotEqual(node.value, deprecated_keyword, path)
                elif isinstance(node, ast.Attribute):
                    self.assertNotEqual(node.attr, "async_get_device", path)

    def test_all_tracker_platforms_inherit_shared_device_info(self):
        for platform, entity_class in (
            ("device_tracker", "SweTrackDeviceTracker"),
            ("sensor", "SweTrackSensor"),
            ("binary_sensor", "SweTrackBinarySensor"),
        ):
            tree = ast.parse((COMPONENT / f"{platform}.py").read_text(encoding="utf-8"))
            entity = next(
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == entity_class
            )
            self.assertIn(
                "SweTrackEntity", [ast.unparse(base) for base in entity.bases]
            )
            self.assertFalse(
                any(
                    isinstance(node, ast.FunctionDef) and node.name == "device_info"
                    for node in entity.body
                )
            )


if __name__ == "__main__":
    unittest.main()
