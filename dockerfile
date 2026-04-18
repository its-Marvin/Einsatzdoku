FROM ubuntu:latest
LABEL org.opencontainers.image.authors="marvin@todtenhofer.de"
LABEL org.opencontainers.image.description="Einsatzdoku - A documentation tool for emergency services"
LABEL org.opencontainers.image.licenses="MIT"
LABEL name="Einsatzdoku"
LABEL version="1.0.2"
# Update and install required software and add user
RUN apt update \
&& apt upgrade -y \
&& apt install -y python3 python3-pip python3-venv \
&& rm -rf /var/lib/apt/lists/* \
&& adduser doku \
&& usermod -a -G www-data doku \
&& mkdir /app

# Add app
WORKDIR /app
COPY . .
RUN chown -R doku:www-data /app \
&& python3 -m venv venv \
&& . venv/bin/activate \
&& pip install --no-cache-dir -r requirements.txt \
&& chmod +x /app/entrypoint.sh
ENV PATH="/app/venv/bin:${PATH}"
EXPOSE 8000
USER doku
ENTRYPOINT [ "/app/entrypoint.sh" ]
#CMD ["daphne", "einsatzdoku.asgi:application", "-b", "0.0.0.0"]