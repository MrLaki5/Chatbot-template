set -e
export CC=gcc

# get desired nginx version (stable branch; check nginx.org/en/security_advisories.html when bumping)
NGINX_VERSION=1.30.6
wget https://nginx.org/download/nginx-$NGINX_VERSION.tar.gz
tar xzvf nginx-$NGINX_VERSION.tar.gz
cd nginx-$NGINX_VERSION

# --with-stream + --with-stream_ssl_module: TLS termination for the RabbitMQ AMQP
# port. AMQP is raw TCP (not HTTP), so it is proxied via the stream module, not http.
./configure --with-http_ssl_module --with-stream --with-stream_ssl_module
make

# install and finish
make install

# check
/usr/local/nginx/sbin/nginx -v
# nginx version: nginx/1.30.6

# Create chron job that activates once per month to renew certificates. The
# certificate is first issued with --standalone (see letsencrypt_cert_gen.sh), but
# by renewal time nginx owns port 80, so renewals go through the webroot instead:
# both nginx configurations serve /.well-known/acme-challenge from /var/www/certbot.
echo "0 3 1 * * certbot renew --webroot -w /var/www/certbot && /usr/local/nginx/sbin/nginx -s reload" | crontab -
