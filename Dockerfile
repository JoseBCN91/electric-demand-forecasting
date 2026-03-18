FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

# AQUÍ ESTÁ EL CAMBIO CRÍTICO: Usamos requirements.txt
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY --chown=user . .

RUN chmod +x run.sh

EXPOSE 7860

CMD ["./run.sh"]
