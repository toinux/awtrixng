#!/bin/env sh
./minify-berry.py anothertime.ax > compact.ax
curl -H "Content-Type: text/plain" -X PUT --data-binary @compact.ax http://192.168.1.202/api/v1/apps/script/Anothertime
