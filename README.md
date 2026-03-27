# Temperature Monitor — Raspberry Pi

Sistema di logging e visualizzazione in tempo reale delle temperature di tre batterie, tramite sensori DS18B20 collegati al bus 1-Wire.

---

## Struttura del progetto

```
Logger/
├── temperature_logger.py   # Legge i sensori e scrive il CSV
├── interface.py            # Grafico + pannello log in tempo reale
├── start.sh                # Avvia tutto in finestre separate
├── stop.sh                 # (generato da start.sh) Ferma tutto
├── venv/                   # Virtualenv Python
└── logged_data/
    └── YYYY-MM-DD/
        └── temperature_log_YYYYMMDD_HHMMSS.csv
```

---

## Requisiti

### Hardware
- Raspberry Pi con GPIO
- Sensori DS18B20 collegati al bus 1-Wire (GPIO pin 4 di default)
- LED di segnalazione sui pin 11, 13, 15

### Software
- Python 3
- Virtualenv con i pacchetti `matplotlib` e `w1thermsensor`
- Terminale grafico: `lxterminal`, `xterm`, `gnome-terminal` o `konsole`

### Abilitare il bus 1-Wire
Aggiungere a `/boot/config.txt`:
```
dtoverlay=w1-gpio
```
Poi riavviare. Verificare che i sensori siano rilevati:
```bash
ls /sys/bus/w1/devices/
```

---

## Installazione

```bash
# 1. Clona o copia la cartella del progetto
cd ~/Desktop/Logger

# 2. Crea il virtualenv
python3 -m venv venv

# 3. Installa le dipendenze (con sudo perché il logger gira come root)
sudo venv/bin/python3 -m pip install matplotlib w1thermsensor
```

---

## Utilizzo

### Avvio
```bash
./start.sh
```
Apre due finestre di terminale separate: una per il logger e una per l'interfaccia grafica. Verifica automaticamente le dipendenze e le installa se mancanti.

### Stop
```bash
./stop.sh
```
Ferma entrambi i processi. Il file `stop.sh` viene generato automaticamente da `start.sh` ad ogni avvio.

### Avvio manuale (senza start.sh)
```bash
# Terminale 1 — logger
sudo venv/bin/python3 temperature_logger.py

# Terminale 2 — interfaccia
sudo venv/bin/python3 interface.py
```

### Aprire un log precedente
```bash
sudo venv/bin/python3 interface.py logged_data/2025-03-27/temperature_log_20250327_143022.csv
```

---

## Sensori configurati

| ID sensore     | Etichetta           | Pin LED | Soglia allarme |
|----------------|---------------------|---------|----------------|
| 000008abfdaf   | Batteria principale | 13      | 54 °C (90% di 60°C) |
| 000008ae137d   | Batteria secondaria | 15      | 72 °C (90% di 80°C) |
| 000008ac6b12   | Batteria ausiliaria | 11      | 72 °C (90% di 80°C) |

Per aggiungere o modificare un sensore, editare il dizionario `sensor_mapping` in `temperature_logger.py` e `SENSOR_LABELS` / `MAX_TEMPS` in `interface.py`.

---

## File CSV

Ogni sessione di logging crea un nuovo file CSV con il timestamp di avvio nel nome:

```
logged_data/2025-03-27/temperature_log_20250327_143022.csv
```

Formato:
```
timestamp,sensor_name,temperature
2025-03-27T14:30:22.123456,Temperature_1_000008abfdaf,38.50
2025-03-27T14:30:23.145678,Temperature_2_000008ae137d,41.25
...
```

I file appartengono all'utente `pi` e possono essere eliminati senza `sudo`.

Il file `logged_data/.current_log` contiene il path del CSV della sessione attiva, usato da `interface.py` per trovarlo automaticamente.

---

## Note tecniche

- Il logger richiede `sudo` per accedere al bus 1-Wire e ai GPIO. I file vengono riassegnati all'utente `pi` tramite `os.chown()` subito dopo la creazione, quindi sono eliminabili normalmente.
- Tutti i path sono assoluti basati sulla posizione dello script (`__file__`), quindi funzionano correttamente anche se `sudo` cambia la working directory a `/root`.
- L'interfaccia si aggiorna ogni 2 secondi (`REFRESH_INTERVAL` in `interface.py`).
- Il pannello log mostra le ultime 10 letture, dalla più recente in cima, con opacità decrescente per le righe più vecchie.
