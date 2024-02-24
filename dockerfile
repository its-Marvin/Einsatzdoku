FROM ubuntu:latest
LABEL org.opencontainers.image.authors="marvin@todtenhofer.de"
# Update and install required software and add user
RUN apt update \
&& apt upgrade -y \
&& apt install -y \
python3 \
python3-pip \
&& rm -rf /var/lib/apt/lists/* \
&& adduser doku \
&& usermod -a -G www-data doku \
&& mkdir /app

# Add app
WORKDIR /app
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt \
&& chown -R doku:www-data /app && chmod +x /app/entrypoint.sh
EXPOSE 8000
USER doku
ENTRYPOINT [ "/app/entrypoint.sh" ]
#CMD ["daphne", "einsatzdoku.asgi:application", "-b", "0.0.0.0"]