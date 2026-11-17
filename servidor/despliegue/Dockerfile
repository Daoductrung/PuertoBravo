# Servidor en línea de Puerto Bravo: Ley del Asfalto
#
# Se construye desde la carpeta que contiene la carpeta servidor (la del código), este Dockerfile y docker-compose.yml:
#     docker compose up -d --build
# No necesita nada más que Python: el servidor solo usa la biblioteca de serie.
FROM python:3.12-slim
RUN useradd --uid 991 --create-home puertobravo && mkdir /datos && chown puertobravo /datos
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY servidor /app/servidor
COPY entrada_docker.sh /app/entrada_docker.sh
VOLUME /datos
EXPOSE 47820
# La configuración y todo lo que se guarda van en /datos, fuera del contenedor: así sobreviven a las actualizaciones.
# El arranque está en entrada_docker.sh: prepara la carpeta de datos, suelta los privilegios y arranca el servidor.
CMD ["sh", "/app/entrada_docker.sh"]
