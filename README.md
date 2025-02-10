# FHV A5-Noten - Home Assistant

Diese Home Assistant Integration ermöglicht es, Noten der FHV (Fachhochschule Vorarlberg) aus dem A5-System abzurufen und als Sensoren in Home Assistant darzustellen.

## 📌 Funktionen
- **Automatische Anmeldung** am FHV A5-Portal
- **Abruf der aktuellen Noten** aus dem Notensystem
- **Darstellung als Sensoren** in Home Assistant

## 🔧 Installation

1. Lade den Ordner `custom_components/homeassistant_a5_noten/` mit allen Dateien in das `custom_components/`-Verzeichnis deines Home Assistant Setups hoch.
2. Füge die folgende Konfiguration in deine `configuration.yaml` ein:

```yaml
sensor:
  - platform: homeassistant_a5_noten
    username: "dein_username"
    password: "dein_passwort"
```

3. Starte Home Assistant erneut.

## ⚙️ Konfigurationsoptionen

| Option             | Beschreibung                                        | Erforderlich | Standardwert |
|-------------------|------------------------------------------------|-------------|-------------|
| `username`       | Dein FHV A5-Benutzername                     | ✅ Ja        | -           |
| `password`       | Dein FHV A5-Passwort                         | ✅ Ja        | -           |
| `scan_interval`  | Aktualisierungsintervall                     | ❌ Nein      | `1 Stunde`  |

## 📊 Verfügbare Sensor-Attribute

Jeder erstellte Sensor repräsentiert ein Modul und enthält die folgenden Attribute:

- `status`: Status der Prüfung (Bestanden, Offen, etc.)
- `note`: Die erhaltene Note
- `bewertung`: Erreichte Punktzahl (falls verfügbar)
- `semester`: Das Semester, in dem die Note vergeben wurde
- `durchschnitt`: Durchschnittliche Bewertung des Moduls
- `credits`: Anzahl der Credits für das Modul

## 🔄 Aktualisierung der Noten

Die Noten werden mit einem Standard-Intervall von **1 Stunde** aktualisiert Falls gewünscht, kann dieses Intervall in der `configuration.yaml` angepasst werden.


## 🖥️ Beispiel-Einbindung in Homeassistant

> **Hinweis:** Für diese Visualisierung werden die Erweiterungen [`auto-entities`](https://github.com/thomasloven/lovelace-auto-entities) und [`flex-table-card`](https://github.com/custom-cards/flex-table-card) benötigt.
> Diese Erweiterungen werden am besten mir HASC Installiert.
> Weitere Informationen zu HACS: [Home Assistant Community Store (HACS)](https://hacs.xyz/)

```yaml
type: grid
cards:
  - type: custom:auto-entities
    filter:
      include:
        - entity_id: sensor.fhv_noten_*
    card:
      type: custom:flex-table-card
      title: Noten
      columns:
        - name: Modul
          data: friendly_name
        - name: Note
          data: state
        - name: Status
          data: status
        - name: Punkte
          data: bewertung
        - name: Semester
          data: semester
        - name: Durchschnitt
          data: durchschnitt
        - name: Credits
          data: credits
    grid_options:
      columns: full
      rows: auto
column_span: 2
```