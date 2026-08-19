# Generate a self-signed certificate on first start if none exists yet. The
# certs live in /certificates, which is bind-mounted from ./nginx/certificates
# on the host, so they persist across rebuilds and are never committed. The
# Let's Encrypt flow uses a separate store (/etc/letsencrypt) and is unaffected.
CERT_DIR=/certificates
if [ ! -f "$CERT_DIR/serverKey.pem" ] || [ ! -f "$CERT_DIR/server.pem" ]; then
    echo "No self-signed certificate found in $CERT_DIR - generating one..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
        -keyout "$CERT_DIR/serverKey.pem" \
        -out "$CERT_DIR/server.pem" \
        -subj "/CN=localhost"
fi

/usr/local/nginx/sbin/nginx -c /nginx_no_letsencrypt.conf
