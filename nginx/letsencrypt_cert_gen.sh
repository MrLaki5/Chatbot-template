# Write pid of nginx to file
touch /run/nginx.pid
pidof nginx > /run/nginx.pid
# Create root dir for acme challange
mkdir -p /var/www/certbot/.well-known/acme-challenge/
# Generate certificates
certbot certonly --webroot -w /var/www/certbot/ -d example.com -m info@example.com --agree-tos -n
# Change configuration on nginx
cat /nginx_letsencrypt.conf > /nginx_no_letsencrypt.conf
# Restart nginx
/usr/local/nginx/sbin/nginx -s reload
# Start cron certificate renewal (defined in init.sh on container creation)
echo "service cron start" >> /run.sh
service cron start

# list certificates -> certbot certificates
# renew certs test (no changes) -> certbot renew --dry-run
# renew certs real, skip if not time -> certbot renew
# certbot renew force renewal -> certbot renew --force-renewal
# Things to do on auto renew -> certbot renew && /usr/local/nginx/sbin/nginx -s reload
