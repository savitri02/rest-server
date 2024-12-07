#!/bin/sh
source .venv/bin/activate
export FLASK_DEBUG=1
export FLASK_APP=main.py
python -m flask run --host=0.0.0.0 --port=5000
