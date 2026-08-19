# base image
FROM ubuntu:22.04

RUN apt-get update && \
    apt-get -y install apt-utils

# install libs
ENV DEBIAN_FRONTEND=noninteractive;
ENV DEBCONF_NONINTERACTIVE_SEEN=true;
RUN apt-get update && apt-get -yq install git wget gcc libpcre3 libpcre3-dev zlib1g zlib1g-dev make libssl-dev openssl python3-certbot-nginx cron

# add init.sh
COPY ./init.sh entrypoint.sh
COPY ./letsencrypt_cert_gen.sh lets_enc.sh
COPY ./run.sh run.sh
RUN chmod +x entrypoint.sh
RUN chmod +x lets_enc.sh
RUN chmod +x run.sh

# run server
RUN /bin/bash -c "./entrypoint.sh"

# Self-signed certs are NOT baked into the image. run.sh generates them at
# startup into /certificates (bind-mounted from the host) if absent, so private
# keys are never committed and survive rebuilds.

# Copy configurations
ADD ./nginx_no_letsencrypt.conf /
ADD ./nginx_letsencrypt.conf /

CMD ["/bin/bash", "-c", "./run.sh"]
