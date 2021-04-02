#!/usr/bin/env bash
ip_addr=$(ip -o route get to 8.8.8.8 | sed -n 's/.*src \([0-9.]\+\).*/\1/p')
gunicorn -t 600 -w 10 -b $ip_addr:5000 --log-level=info app:app