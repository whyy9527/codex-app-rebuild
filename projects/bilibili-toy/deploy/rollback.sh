#!/bin/sh
set -eu
STAGING=$1
BASE=/opt/bilibili-toy
PROXY=/clouddream/nginx-proxy-manage/data/nginx/proxy_host/bilibili-toy-s16.conf
case "$STAGING" in /var/tmp/bilibili-toy-s16-*) ;; *) exit 1;; esac
if [ -s "$STAGING/previous-release" ]; then
    ln -s "$(cat "$STAGING/previous-release")" "$BASE/current.rollback"
    mv -Tf "$BASE/current.rollback" "$BASE/current"
    if [ -f "$STAGING/previous-service" ]; then cp "$STAGING/previous-service" /etc/systemd/system/bilibili-toy-s16.service; fi
    systemctl daemon-reload
    systemctl restart bilibili-toy-s16.service
else
    systemctl disable --now bilibili-toy-s16.service
    systemctl disable --now bilibili-toy-s16-renew.timer
fi
if [ -f "$STAGING/previous-proxy.conf" ]; then cp "$STAGING/previous-proxy.conf" "$PROXY"; else rm -f "$PROXY"; fi
docker exec nginx-app nginx -t
docker exec nginx-app nginx -s reload
