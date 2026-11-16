# Dimplex Wärmepumpe in Home Assistant

Custom Component zur Integration von Dimplex Wärmepumpen (getestet mit "System M") in Home Assistant über die Dimplex Home Cloud API.

## ✨ Features

- 🔐 **Einfacher Login** - Mit Benutzername/Passwort (wie in der Dimplex App)
- 🔄 **Automatischer Token Refresh** - OAuth2 Tokens werden automatisch erneuert
- 📱 **Automatische Geräteerkennung** - Wähle dein Gerät aus einer Liste
- 🌡️ **30+ Sensoren** - Temperaturen, Lüftung, Verdichter-Statistiken
- 🎛️ **Dimplex Air** - Steuerung angeschlossener Dimplex Air Wohnraumlüftungen (Lüftungsstufen und Bypass-Schalter)

## 📦 Unterstützte Geräte

Diese Integration wurde getestet mit:

- **Dimplex System M** (Split 9) + **System M Air**
- Weitere Dimplex Wärmepumpen mit Home Cloud Anbindung könnten ebenfalls funktionieren

## 🚀 Installation

### HACS (empfohlen)

1. Öffne HACS in Home Assistant
2. Klicke auf **Integrationen**
3. Klicke auf die drei Punkte oben rechts → **Benutzerdefinierte Repositories**
4. Füge hinzu:
   - **Repository**: `https://github.com/ay-kay/homeassistant-dimplex`
   - **Kategorie**: Integration
5. Klicke auf **Hinzufügen**
6. Suche nach "Dimplex" und klicke auf **Herunterladen**
7. **Starte Home Assistant neu**

### Manuelle Installation

1. Lade das [neueste Release](https://github.com/ay-kay/homeassistant-dimplex/releases) herunter
2. Entpacke und kopiere den `custom_components/dimplex` Ordner nach `config/custom_components/`
3. Starte Home Assistant neu

## ⚙️ Konfiguration

1. Gehe zu **Einstellungen → Geräte & Dienste**
2. Klicke auf **+ Integration hinzufügen**
3. Suche nach **"Dimplex"**
4. Wähle **"Mit Benutzername und Passwort anmelden"**
5. Gib deine Dimplex-Kontodaten ein (die gleichen wie in der Dimplex App)
6. Wähle dein Gerät aus der Liste

## 📊 Entities

### Sensoren - Temperaturen

| Entity | Beschreibung |
|--------|--------------|
| `sensor.dimplex_heat_pump_temperature_warmwater` | Warmwasser Temperatur |
| `sensor.dimplex_heat_pump_temperature_supply` | Vorlauf Temperatur |
| `sensor.dimplex_heat_pump_temperature_return` | Rücklauf Temperatur |
| `sensor.dimplex_heat_pump_temperature_hk_target` | Heizkreis Solltemperatur |
| `sensor.dimplex_heat_pump_temperature_hk_actual` | Heizkreis Isttemperatur |
| `sensor.dimplex_heat_pump_temperature_room_target` | Raum Solltemperatur |
| `sensor.dimplex_heat_pump_temperature_room_actual` | Raum Isttemperatur |
| `sensor.dimplex_heat_pump_temperature_dewpoint` | Taupunkt |

### Sensoren - Lüftung

| Entity | Beschreibung |
|--------|--------------|
| `sensor.dimplex_heat_pump_vent_temp_outside` | Außenluft Temperatur |
| `sensor.dimplex_heat_pump_vent_temp_supply` | Zuluft Temperatur |
| `sensor.dimplex_heat_pump_vent_temp_exhaust` | Abluft Temperatur |
| `sensor.dimplex_heat_pump_vent_temp_outgoing` | Fortluft Temperatur |
| `sensor.dimplex_heat_pump_vent_humidity_exhaust` | Abluft Feuchtigkeit |
| `sensor.dimplex_heat_pump_vent_humidity_outside` | Außenluft Feuchtigkeit |
| `sensor.dimplex_heat_pump_vent_voc_exhaust` | Abluft VOC |
| `sensor.dimplex_heat_pump_vent_filter_days` | Filterrestlaufzeit (Tage) |
| `sensor.dimplex_heat_pump_vent_exhaust_flow` | Abluft Volumenstrom |
| `sensor.dimplex_heat_pump_vent_supply_flow` | Zuluft Volumenstrom |

### Sensoren - Verdichter

| Entity | Beschreibung |
|--------|--------------|
| `sensor.dimplex_heat_pump_compressor_runtime` | Verdichter Laufzeit (Stunden) |
| `sensor.dimplex_heat_pump_compressor_clocks_total` | Verdichter Takte Gesamt |
| `sensor.dimplex_heat_pump_compressor_clocks_heating` | Verdichter Takte Heizung |
| `sensor.dimplex_heat_pump_compressor_clocks_hotwater` | Verdichter Takte Warmwasser |
| `sensor.dimplex_heat_pump_compressor_status` | Verdichter Status |
| `sensor.dimplex_heat_pump_block_reason` | Sperrgrund der Wärmepumpe (z. B. EVU Sperre, Hochdruck) |
| `sensor.dimplex_heat_pump_fault` | Störung (Rohwert) |

### Steuerung

| Entity | Beschreibung |
|--------|--------------|
| `switch.dimplex_heat_pump_ventilation_bypass` | Lüftung Bypass ein/aus |
| `select.dimplex_heat_pump_ventilation_mode` | Lüftungsstufe (Off/Auto/Level 1-3) |


## 🔧 Troubleshooting

### Login funktioniert nicht

Die Integration verwendet den gleichen Auth-Flow wie die Dimplex App:
- Prüfe, ob du dich mit den gleichen Daten in der Dimplex App anmelden kannst
- Verwende die manuelle Token-Methode als Fallback

### Keine Geräte gefunden

Falls die automatische Geräteerkennung fehlschlägt:
1. Wähle "Manuell mit Refresh Token" beim Setup
2. Die Device ID findest du in der Dimplex App unter Geräteeinstellungen
3. Format: `sn-UHI-mac-XX-XX-XX-XX-XX-XX`

### Token abgelaufen

Bei abgelaufenem Token erscheint eine Benachrichtigung. Klicke darauf und melde dich neu an.

### Debug-Logging aktivieren

Füge folgendes zu `configuration.yaml` hinzu:

```yaml
logger:
  default: info
  logs:
    custom_components.dimplex: debug
```

## ⚠️ Disclaimer

Diese Integration ist ein inoffizielles Community-Projekt und steht in keiner Verbindung zu Glen Dimplex. Die Nutzung erfolgt auf eigene Gefahr.
