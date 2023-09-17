#!/usr/bin/env bash

# Deploy to local ip at port 5005

gunicorn -b "0.0.0.0:5005" -w 4 'server:app'
