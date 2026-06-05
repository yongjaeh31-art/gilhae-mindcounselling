#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install flask
python3 app.py
