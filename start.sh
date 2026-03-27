#!/bin/bash

sudo venv/bin/python3 temperature_logger.py &

# Aspetta che il file venga creato
while [ ! -f "output.txt" ]; do
    sleep 0.5
done

sudo venv/bin/python3 interface.py &

wait