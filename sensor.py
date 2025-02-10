from datetime import datetime, timedelta
import logging

from bs4 import BeautifulSoup
import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = timedelta(hours=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config,
    add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Set up A5-Noten Platform."""
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    scan_interval = config[CONF_SCAN_INTERVAL]

    data = FhvNotenData(
        username=username,
        password=password,
    )

    data.update()
    if not data.modules_data:
        _LOGGER.warning("FHV A5: Keine Module gefunden oder Login schlug fehl")

    sensors = []
    for modul_name in data.modules_data:
        sensor = FhvNotenSensor(data=data, modul_name=modul_name)

        sensor.scan_interval = scan_interval
        sensors.append(sensor)

    add_entities(sensors, True)


class FhvNotenData:
    LOGIN_URL = "https://a5.fhv.at/ajax/120/LoginResponsive/LoginHandler"
    NOTEN_URL = "https://a5.fhv.at/de/noten.php"

    def __init__(self, username, password):
        self._username = username
        self._password = password

        self.modules_data = {}

        self._last_update = None
        self._cache_interval = timedelta(seconds=60)

    def update(self):
        now = datetime.now()
        if self._last_update and (now - self._last_update < self._cache_interval):
            return

        try:
            session = requests.Session()
            payload = {
                "username": self._username,
                "password": self._password,
                "domain-id": 8,
                "permanent-login": 0,  # Permanenter Login '1' funktioniert leider nicht...
            }

            resp_login = session.post(self.LOGIN_URL, data=payload)
            if resp_login.status_code != 200:
                _LOGGER.error(
                    "FHV A5: Login fehlgeschlagen (HTTP %s)", resp_login.status_code
                )
                return

            resp_noten = session.get(self.NOTEN_URL)
            if resp_noten.status_code != 200:
                _LOGGER.error(
                    "FHV A5: Notenseite konnte nicht geladen werden (HTTP %s)",
                    resp_noten.status_code,
                )
                return

            entries = self._parse_noten_html(resp_noten.text)
            unique_mods = self._remove_duplicates(entries)

            new_data = {}
            for e in unique_mods:
                modul = e.get("Modul", "")
                if not modul:
                    continue

                new_data[modul] = {
                    "status": e.get("Status", ""),
                    "note": e.get("Note", ""),
                    "bewertung": e.get("Bewertung", "").replace("Bewertung folgt", "-"),
                    "semester": e.get("Semester", ""),
                    "durchschnitt": e.get("Durchschnitt", ""),
                    "credits": e.get("Credits", ""),
                }
            self.modules_data = new_data
            self._last_update = now

        except Exception as exc:
            _LOGGER.error("FHV A5: Fehler beim Update: %s", exc)

    def _parse_noten_html(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table", class_="table table-bordered table-update")
        results = []

        for table in tables:
            tbody = table.find("tbody")
            if not tbody:
                continue

            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                raw_cols = [td.get_text(strip=True) for td in cols]

                if len(raw_cols) < 2:
                    continue
                status = raw_cols[1]
                if not status:
                    continue

                keys = [
                    "Modul",
                    "Status",
                    "Note",
                    "Bewertung",
                    "Teilbewertung",
                    "Credits",
                    "Versuch",
                    "Datum",
                    "Semester",
                    "Durchschnitt",
                    "Anerkennung",
                ]
                entry = {}
                for i, k in enumerate(keys):
                    if i < len(raw_cols):
                        entry[k] = raw_cols[i]
                    else:
                        entry[k] = ""
                results.append(entry)
        return results

    def _remove_duplicates(self, entries):
        unique_list = []
        seen = set()
        for e in entries:
            modul_name = e.get("Modul", "")
            if modul_name and modul_name not in seen:
                seen.add(modul_name)
                unique_list.append(e)
        return unique_list


class FhvNotenSensor(SensorEntity):
    def __init__(self, data: FhvNotenData, modul_name):
        self._data = data
        self._modul_name = modul_name
        self._state = None
        self._attributes = {}

        self._name = modul_name
        self._unique_id = f"fhv_noten_{modul_name}"
        self.entity_id = f"sensor.{self.unique_id}"

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    # Note
    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    def update(self):
        self._data.update()
        info = self._data.modules_data.get(self._modul_name, {})
        self._state = info.get("note", "")

        self._attributes = {
            "status": info.get("status", ""),
            "bewertung": info.get("bewertung", ""),
            "semester": info.get("semester", ""),
            "durchschnitt": info.get("durchschnitt", ""),
            "credits": info.get("credits", ""),
        }
