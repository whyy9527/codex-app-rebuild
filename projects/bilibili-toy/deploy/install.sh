#!/bin/sh
set -eu
STAGING=$1
RELEASE=$2
GATEWAY=$3
BASE=/opt/bilibili-toy
PROXY=/clouddream/nginx-proxy-manage/data/nginx/proxy_host/bilibili-toy-s16.conf
mkdir -p "$BASE/releases/$RELEASE"
tar -xzf "$STAGING/site.tar.gz" -C "$BASE/releases/$RELEASE"
cd "$BASE/releases/$RELEASE"
sha256sum -c checksums.txt > "$STAGING/release-verification.log"
# The service account can read the release but cannot alter it.
find . -type d -exec chmod 755 {} +
find . -type f -exec chmod 644 {} +
[ ! -e "$BASE/current" ] || readlink -f "$BASE/current" > "$STAGING/previous-release"
[ ! -f "$PROXY" ] || cp -a "$PROXY" "$STAGING/previous-proxy.conf"
[ ! -f /etc/systemd/system/bilibili-toy-s16.service ] || cp -a /etc/systemd/system/bilibili-toy-s16.service "$STAGING/previous-service"
sed "s/__GATEWAY__/$GATEWAY/g" deploy/s16.service > /etc/systemd/system/bilibili-toy-s16.service
ln -s "$BASE/releases/$RELEASE" "$BASE/current.next"
mv -Tf "$BASE/current.next" "$BASE/current"
systemctl daemon-reload
systemctl enable --now bilibili-toy-s16.service
systemctl restart bilibili-toy-s16.service
for attempt in $(seq 1 20); do
    if curl -fsS "http://$GATEWAY:18086/release.json" > "$STAGING/origin-release.json"; then break; fi
    sleep 1
done
curl -fsS "http://$GATEWAY:18086/content/assets/local-index.js" -o /dev/null
docker exec nginx-app curl -fsS "http://$GATEWAY:18086/release.json"
docker exec nginx-app test -f /etc/letsencrypt/live/bilibili-toy-s16/fullchain.pem || {
    printf 'Install the S16 DNS-01 certificate with tools.certificate before publishing.\n' >&2
    exit 1
}
cat deploy/s16.http.conf > "$PROXY"
sed "s/__GATEWAY__/$GATEWAY/g" deploy/s16.https.conf >> "$PROXY"
if ! docker exec nginx-app nginx -t; then
    cp deploy/s16.http.conf "$PROXY"
    docker exec nginx-app nginx -t
    docker exec nginx-app nginx -s reload
    exit 1
fi
docker exec nginx-app nginx -s reload
systemctl is-active bilibili-toy-s16.service
# Check the existing shared services after activation.
docker inspect --format '{{.Name}} {{.State.Health.Status}}' xinxia-landing media-workflow-app-1
curl -fsS https://landing.xinxiayiyan.com/ -o /dev/null
printf 'Release ready: %s\n' "$RELEASE"
