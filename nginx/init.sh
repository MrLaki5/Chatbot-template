export CC=gcc

# get desired nginx version
wget http://nginx.org/download/nginx-1.25.1.tar.gz
tar xzvf nginx-1.25.1.tar.gz
cd nginx-1.25.1

# --with-stream + --with-stream_ssl_module: TLS termination for the RabbitMQ AMQP
# port. AMQP is raw TCP (not HTTP), so it is proxied via the stream module, not http.
./configure --with-http_ssl_module --with-stream --with-stream_ssl_module
make

# install and finish
make install

# check
/usr/local/nginx/sbin/nginx -v
# nginx version: nginx/1.25.1

# Create chron job that activates once per month to renew certificates
echo "0 3 1 * * certbot renew && /usr/local/nginx/sbin/nginx -s reload" | crontab -
