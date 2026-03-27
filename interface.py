"""
Realtime temperature plot — lancia questo MENTRE gira il tuo script di logging.
Passa il path del CSV come argomento, oppure lo cerca automaticamente.

    python realtime_plot.py
    python realtime_plot.py temperature_log_20240101_120000.csv
"""

import sys
import glob
import datetime
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
import time

SENSOR_LABELS = {
    "Temperature_1_000008abfdaf": "Batteria principale",
    "Temperature_2_000008ae137d": "Batteria secondaria",
    "Temperature_3_000008ac6b12": "Batteria ausiliaria",
}
MAX_TEMPS = {
    "Temperature_1_000008abfdaf": 0.9 * 60,
    "Temperature_2_000008ae137d": 0.9 * 80,
    "Temperature_3_000008ac6b12": 0.9 * 80,
}
COLORS = ["#378ADD", "#1D9E75", "#D85A30"]
REFRESH_INTERVAL = 2  # secondi


def find_latest_csv():
    files = glob.glob("logged_data/temperature_log_*.csv")
    if not files:
        return None
    return max(files)  # ordine lessicografico = più recente


def read_csv(path):
    data = defaultdict(lambda: {"times": [], "temps": []})
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.datetime.fromisoformat(row["timestamp"])
                    sensor = row["sensor_name"]
                    temp = float(row["temperature"])
                    data[sensor]["times"].append(ts)
                    data[sensor]["temps"].append(temp)
                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        pass
    return data


def main():
    # Trova il CSV
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = find_latest_csv()
        if csv_path is None:
            print("Nessun file temperature_log_*.csv trovato nella cartella corrente.")
            print("Avvia prima lo script di logging, oppure passa il path come argomento.")
            sys.exit(1)
    print(f"Leggendo: {csv_path}")

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.canvas.manager.set_window_title("Temperature Monitor — Realtime")
    plt.ion()

    lines = {}

    while True:
        data = read_csv(csv_path)
        sensors = list(data.keys())

        ax.cla()
        ax.set_facecolor("#111111")
        fig.patch.set_facecolor("#111111")

        for i, sensor in enumerate(sensors):
            times = data[sensor]["times"]
            temps = data[sensor]["temps"]
            if not times:
                continue
            color = COLORS[i % len(COLORS)]
            label = SENSOR_LABELS.get(sensor, sensor)
            ax.plot(times, temps, color=color, linewidth=1.8, label=label)

            # Ultimo valore come annotazione
            last_t, last_v = times[-1], temps[-1]
            max_t = MAX_TEMPS.get(sensor, None)
            warn = max_t and last_v >= max_t
            ax.annotate(
                f" {last_v:.1f}°C{'  ⚠' if warn else ''}",
                xy=(last_t, last_v),
                color=color,
                fontsize=9,
                va="center",
            )

            # Linea soglia
            if max_t:
                ax.axhline(
                    max_t,
                    color=color,
                    linewidth=0.6,
                    linestyle="--",
                    alpha=0.4,
                )

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=30)

        ax.set_ylabel("Temperatura (°C)", color="#aaaaaa", fontsize=10)
        ax.tick_params(colors="#aaaaaa", labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333333")
        ax.grid(color="#222222", linewidth=0.5)

        if sensors:
            ax.legend(
                loc="upper left",
                fontsize=9,
                framealpha=0.3,
                facecolor="#222222",
                edgecolor="#444444",
            )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        ax.set_title(
            f"Temperature sensori  ·  aggiornato {now_str}",
            color="#cccccc",
            fontsize=11,
            pad=10,
        )

        plt.tight_layout()
        plt.pause(REFRESH_INTERVAL)

        if not plt.get_fignums():
            break  # finestra chiusa


if __name__ == "__main__":
    main()