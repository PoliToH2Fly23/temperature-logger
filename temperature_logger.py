import datetime
import time
import sys
import csv
import os
import w1thermsensor
from w1thermsensor import W1ThermSensor

sensor_mapping = {
    "000008abfdaf": { # Main battery originale
        "name": "Temperature_1_000008abfdaf", 
        "ledPin" : 13,
        "sensor" : None,
        "maxTemperature" : 0.9*60
    },
    "000008ae137d": { # Future secondary battery
        "name": "Temperature_2_000008ae137d",
        "ledPin" : 15,
        "sensor" : None,
        "maxTemperature" : 0.9*80
    },
    "000008ac6b12": { # Auxiliary battery
        "name" : "Temperature_3_000008ac6b12", 
        "ledPin" : 11,
        "sensor" : None,
        "maxTemperature" : 0.9*80
    }
}


# =========================
# FILE CSV CON TIMESTAMP
# =========================
START_TIME = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
import os
os.makedirs("logged_data", exist_ok=True)
CSV_FILE = f"logged_data/temperature_log_{START_TIME}.csv"


def init_csv():
    """Crea il file CSV con header"""
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "sensor_name", "temperature"])


def log_to_csv(sensor_name, temperature):
    """Scrive una riga nel CSV"""
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
            print(f"[{sensor_name}] sensore non pronto (tentativo {attempt})")
        except Exception as e:
            print(
                f"[{sensor_name}] errore di lettura: {e}",
                file=sys.stderr
            )
        time.sleep(0.1)

    print(
        f"[{sensor_name}] lettura fallita dopo {max_attempts} tentativi",
        file=sys.stderr
    )
    return None


# =========================
# MAIN LOOP
# =========================
def main():

    init_csv()
    print(f"Logging avviato su file: {CSV_FILE}")

    sensors = W1ThermSensor.get_available_sensors()
    sensor_data = {}

    while True:
        for sensor in sensors:
            sensor_info = sensor_mapping.get(sensor.id)
            if sensor_info is None:
                continue

            sensor_name = sensor_info.get("name")
            temp = read_temp(sensor, 5, sensor_name)

            if temp is None:
                continue

            sensor_data[sensor_name] = temp
            log_to_csv(sensor_name, temp)

            print(
                f"{datetime.datetime.now().strftime('%H:%M:%S')} | "
                f"{sensor_name}: {temp:.2f} °C"
            )

        time.sleep(1)


if __name__ == "__main__":
    main()
