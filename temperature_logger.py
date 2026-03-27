import datetime
import time
import sys
import csv
import os
import w1thermsensor
from w1thermsensor import W1ThermSensor

# Cartella del progetto — funziona anche se avviato con sudo da un'altra directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

sensor_mapping = {
    "000008abfdaf": {
        "name": "Temperature_1_000008abfdaf",
        "ledPin": 13,
        "sensor": None,
        "maxTemperature": 0.9 * 60,
        "label": "Batteria principale",
    },
    "000008ae137d": {
        "name": "Temperature_2_000008ae137d",
        "ledPin": 15,
        "sensor": None,
        "maxTemperature": 0.9 * 80,
        "label": "Batteria secondaria",
    },
    "000008ac6b12": {
        "name": "Temperature_3_000008ac6b12",
        "ledPin": 11,
        "sensor": None,
        "maxTemperature": 0.9 * 80,
        "label": "Batteria ausiliaria",
    },
}

# =========================
# FILE CSV CON TIMESTAMP
# =========================
_NOW = datetime.datetime.now()
START_TIME = _NOW.strftime("%Y%m%d_%H%M%S")
DATE_DIR = os.path.join(SCRIPT_DIR, "logged_data", _NOW.strftime("%Y-%m-%d"))
# Controlla se la cartella esiste già
first_creation = not os.path.exists(DATE_DIR)

# Crea la cartella
os.makedirs(DATE_DIR, exist_ok=True)

# Se è la prima volta, aggiungi a .gitignore
if first_creation:
    gitignore_path = os.path.join(SCRIPT_DIR, ".gitignore")

    entry = "logged_data/\n"

    # Evita duplicati
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.readlines()
    else:
        content = []

    if entry not in content:
        with open(gitignore_path, "a") as f:
            f.write(entry)
            
CSV_FILE = os.path.join(DATE_DIR, f"temperature_log_{START_TIME}.csv")

CURRENT_LOG_POINTER = os.path.join(SCRIPT_DIR, "logged_data", ".current_log")


def _fix_ownership(path):
    """Riporta il proprietario del file all'utente reale (SUDO_UID/SUDO_GID),
    così i file creati da sudo possono essere eliminati senza permessi root."""
    try:
        uid = int(os.environ.get("SUDO_UID", os.getuid()))
        gid = int(os.environ.get("SUDO_GID", os.getgid()))
        os.chown(path, uid, gid)
    except (PermissionError, ValueError):
        pass  # se non siamo root, il file è già nostro


def init_csv():
    # Assicura che anche logged_data/ e la sottocartella per data
    # appartengano all'utente reale, non a root
    os.makedirs(os.path.dirname(CURRENT_LOG_POINTER), exist_ok=True)
    _fix_ownership(os.path.join(SCRIPT_DIR, "logged_data"))
    _fix_ownership(DATE_DIR)

    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "sensor_name", "temperature"])
    _fix_ownership(CSV_FILE)

    with open(CURRENT_LOG_POINTER, "w") as f:
        f.write(CSV_FILE)
    _fix_ownership(CURRENT_LOG_POINTER)


def log_to_csv(sensor_name, temperature):
    timestamp = datetime.datetime.now().isoformat()
    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, sensor_name, temperature])


# =========================
# LETTURA SENSORE
# =========================
def read_temp(sensor, max_attempts, sensor_name):
    for attempt in range(1, max_attempts + 1):
        try:
            return sensor.get_temperature()
        except w1thermsensor.SensorNotReadyError:
            print(f"  [{sensor_name}] sensore non pronto (tentativo {attempt})")
        except Exception as e:
            print(f"  [{sensor_name}] errore di lettura: {e}", file=sys.stderr)
        time.sleep(0.1)
    print(f"  [{sensor_name}] lettura fallita dopo {max_attempts} tentativi", file=sys.stderr)
    return None


# =========================
# STAMPA RIGA DI LOG
# =========================
WARN_SYMBOL = "  ⚠ ATTENZIONE: soglia quasi raggiunta!"
SEP = "─" * 58


def print_reading(ts_str, label, temp, max_temp):
    warn = temp >= max_temp
    bar_len = 30
    fraction = min(temp / (max_temp / 0.9), 1.0)
    filled = int(fraction * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)
    warn_str = WARN_SYMBOL if warn else ""
    print(f"  {label:<22} {temp:>6.2f} °C  [{bar}]{warn_str}")


# =========================
# MAIN LOOP
# =========================
def main():
    init_csv()
    print(SEP)
    print(f"  Temperature Logger avviato")
    print(f"  Log: {CSV_FILE}")
    print(f"  Premi Ctrl+C per fermare")
    print(SEP)

    sensors = W1ThermSensor.get_available_sensors()

    try:
        while True:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"\n  ⏱  {now_str}")
            any_read = False

            for sensor in sensors:
                sensor_info = sensor_mapping.get(sensor.id)
                if sensor_info is None:
                    continue

                sensor_name = sensor_info["name"]
                label = sensor_info["label"]
                max_temp = sensor_info["maxTemperature"]

                temp = read_temp(sensor, 5, sensor_name)
                if temp is None:
                    continue

                log_to_csv(sensor_name, temp)
                print_reading(now_str, label, temp, max_temp)
                any_read = True

            if not any_read:
                print("  (nessun sensore disponibile)")

            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n{SEP}")
        print("  Logger fermato.")
        print(SEP)


if __name__ == "__main__":
    main()
