#!/usr/bin/env bash
gunicorn -t 600 -w 10  -b 192.168.0.223:5000 app:app