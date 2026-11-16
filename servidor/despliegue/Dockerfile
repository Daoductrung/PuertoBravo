# Servidor en línea de Puerto Bravo: Ley del Asfalto
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends openssl && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 991 --create-home puertobravo
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
WORKDIR /app
COPY servidor /app/servidor
RUN mkdir /datos && chown puertobravo /datos
USER puertobravo
VOLUME /datos
EXPOSE 47820
# La configuración y todo lo que se guarda van en /datos: así sobreviven a las actualizaciones.
CMD ["sh", "-c", "cd /datos && ([ -f servidor.conf ] || python -m servidor --ejemplo) && PYTHONPATH=/app exec python -m servidor servidor.conf"]
