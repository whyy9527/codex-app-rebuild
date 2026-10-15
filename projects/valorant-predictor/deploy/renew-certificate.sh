#!/bin/sh
set -eu
status=0
docker exec nginx-app certbot renew --config /etc/letsencrypt.ini --cert-name valorant-predictor --authenticator webroot --preferred-challenges http --webroot-path /data/letsencrypt-acme-challenge --no-random-sleep-on-renew --quiet || status=$?
docker exec nginx-app nginx -t
docker exec nginx-app nginx -s reload
exit "$status"
