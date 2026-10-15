#!/bin/sh
set -eu
docker exec nginx-app certbot renew --config /etc/letsencrypt.ini --cert-name bilibili-toy-s16 --authenticator webroot --preferred-challenges http --webroot-path /data/letsencrypt-acme-challenge --no-random-sleep-on-renew --quiet
docker exec nginx-app nginx -t
docker exec nginx-app nginx -s reload
