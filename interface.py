"""
Realtime temperature plot con pannello log.

    python interface.py
    python interface.py logged_data/2024-01-01/temperature_log_20240101_120000.csv
"""

import sys
import glob
import datetime
import csv
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
from collections import defaultdict, deque

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
REFRESH_INTERVAL = 2
# Numero righe nel pannello log — abbassato per evitare sovrapposizioni
LOG_MAX_LINES = 10
CURRENT_LOG_POINTER = os.path.join(SCRIPT_DIR, "logged_data", ".current_log")

BG  = "#111111"
BG2 = "#181818"
FG  = "#cccccc"
FG_DIM = "#666666"


def find_latest_csv():
    if os.path.exists(CURRENT_LOG_POINTER):
        try:
            path = open(CURRENT_LOG_POINTER).read().strip()
            if os.path.exists(path):
                return path
        except OSError:
            pass
    # Fallback: cerca ricorsivamente in logged_data/
    files = glob.glob(os.path.join(SCRIPT_DIR, "logged_data", "**", "temperature_log_*.csv"), recursive=True)
    if not files:
        return None
    return max(files)


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


def read_last_rows(path, n):
    rows = []
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reversed(list(deque(reader, maxlen=n))))
    except (FileNotFoundError, KeyError):
        pass
    return rows


def main():
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = find_latest_csv()
        if csv_path is None:
            print("Nessun file temperature_log_*.csv trovato.")
            print("Avvia prima il logger, oppure passa il path come argomento.")
            sys.exit(1)
    print(f"Leggendo: {csv_path}")
    print("Chiudi la finestra o premi Ctrl+C per fermare.")

    plt.style.use("dark_background")
    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(BG)
    fig.canvas.manager.set_window_title("Temperature Monitor — Realtime")

    gs = gridspec.GridSpec(
        2, 1,
        height_ratios=[3, 1],
        hspace=0.06,
        left=0.07, right=0.97,
        top=0.93, bottom=0.05,
    )
    ax_plot = fig.add_subplot(gs[0])
    ax_log  = fig.add_subplot(gs[1])

    # Calcola l'altezza in punti del pannello log per ricavare
    # il passo esatto tra le righe (evita sovrapposizioni)
    fig.canvas.draw()  # necessario per avere bbox valida
    log_bbox   = ax_log.get_window_extent()   # in display points
    log_height = log_bbox.height              # pixel/pt disponibili

    # fontsize in pt → stima altezza riga con interlinea 1.3
    FONT_PT   = 8.5
    LINE_H_PT = FONT_PT * 1.35
    # quante righe entrano davvero (lascia margine header + footer)
    max_rows_fit = max(1, int((log_height * 0.78) / LINE_H_PT))
    n_rows = min(LOG_MAX_LINES, max_rows_fit)
    # passo y in coordinate axes (0‥1)
    row_step = 0.78 / n_rows

    plt.ion()

    try:
        while True:
            # ── Grafico ──────────────────────────────────────────────
            data = read_csv(csv_path)
            sensors = list(data.keys())

            ax_plot.cla()
            ax_plot.set_facecolor(BG)

            for i, sensor in enumerate(sensors):
                times = data[sensor]["times"]
                temps = data[sensor]["temps"]
                if not times:
                    continue
                color = COLORS[i % len(COLORS)]
                label = SENSOR_LABELS.get(sensor, sensor)
                ax_plot.plot(times, temps, color=color, linewidth=1.8, label=label)

                last_t, last_v = times[-1], temps[-1]
                max_t = MAX_TEMPS.get(sensor)
                warn = max_t and last_v >= max_t
                ax_plot.annotate(
                    f" {last_v:.1f}°C{'  ⚠' if warn else ''}",
                    xy=(last_t, last_v),
                    color=color, fontsize=9, va="center",
                )
                if max_t:
                    ax_plot.axhline(max_t, color=color, linewidth=0.6, linestyle="--", alpha=0.4)

            ax_plot.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            ax_plot.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax_plot.tick_params(axis="x", labelbottom=False, colors=FG_DIM, labelsize=8)
            ax_plot.tick_params(axis="y", colors=FG_DIM, labelsize=9)
            for spine in ax_plot.spines.values():
                spine.set_edgecolor("#333333")
            ax_plot.grid(color="#222222", linewidth=0.5)
            ax_plot.set_ylabel("Temperatura (°C)", color=FG_DIM, fontsize=10)
            if sensors:
                ax_plot.legend(loc="upper left", fontsize=9, framealpha=0.3,
                               facecolor="#222222", edgecolor="#444444")
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            ax_plot.set_title(
                f"Temperature sensori  ·  aggiornato {now_str}",
                color=FG, fontsize=11, pad=8,
            )

            # ── Pannello log ─────────────────────────────────────────
            ax_log.cla()
            ax_log.set_facecolor(BG2)
            for spine in ax_log.spines.values():
                spine.set_edgecolor("#2a2a2a")
            ax_log.set_xticks([])
            ax_log.set_yticks([])
            ax_log.set_xlim(0, 1)
            ax_log.set_ylim(0, 1)

            # Intestazione
            ax_log.text(
                0.01, 0.96,
                "  timestamp            sensore                 temp",
                transform=ax_log.transAxes,
                color=FG_DIM, fontsize=FONT_PT - 0.5,
                fontfamily="monospace", va="top",
            )

            rows = read_last_rows(csv_path, n_rows)
            sensor_keys = list(SENSOR_LABELS.keys())

            for j, row in enumerate(rows):
                try:
                    ts         = row["timestamp"][:19]
                    sensor_name = row["sensor_name"]
                    label      = SENSOR_LABELS.get(sensor_name, sensor_name)
                    temp       = float(row["temperature"])
                    max_t      = MAX_TEMPS.get(sensor_name)
                    warn_str   = "  ⚠" if (max_t and temp >= max_t) else ""
                    color      = COLORS[sensor_keys.index(sensor_name) % len(COLORS)] \
                                 if sensor_name in sensor_keys else FG_DIM
                    alpha      = max(0.25, 1.0 - j * (0.75 / n_rows))

                    y = 0.88 - j * row_step
                    line_str = f"  {ts}  {label:<23}  {temp:>6.2f} °C{warn_str}"
                    ax_log.text(
                        0.01, y, line_str,
                        transform=ax_log.transAxes,
                        color=color, fontsize=FONT_PT,
                        fontfamily="monospace",
                        va="top", alpha=alpha,
                    )
                except (ValueError, KeyError):
                    continue

            ax_log.text(
                0.01, 0.02,
                f"  log: {csv_path}",
                transform=ax_log.transAxes,
                color=FG_DIM, fontsize=7.5,
                fontfamily="monospace", va="bottom",
            )

            fig.canvas.draw()
            plt.pause(REFRESH_INTERVAL)

            if not plt.get_fignums():
                break

    except KeyboardInterrupt:
        print("\nInterfaccia fermata.")


if __name__ == "__main__":
    main()
