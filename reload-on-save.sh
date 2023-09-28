#!/usr/bin/env bash

set -x

. venv/bin/activate

while :; do
    inotifywait -e modify .
    python main.py
done
