# Usamos una imagen oficial de Python ligera
FROM python:3.10-slim

# Instalamos dependencias del sistema necesarias para compilar ciertas librerías (como CatBoost)
RUN apt-get update && apt-get install -y \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face Spaces exige que no usemos el usuario 'root'
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Establecemos el directorio de trabajo
WORKDIR /home/user/app

# Copiamos primero el archivo de dependencias para aprovechar la caché de Docker
# (Si usas requirements.txt, descomenta la línea de abajo y comenta la de pyproject.toml)
# COPY --chown=user requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Como vi que tienes un pyproject.toml, instalamos directamente desde ahí:
COPY --chown=user pyproject.toml .
RUN pip install --no-cache-dir .

# Copiamos TODO el resto del código y las bases de datos (mlflow.db, etc.)
COPY --chown=user . .

# Le damos permisos de ejecución a nuestro script de arranque
RUN chmod +x run.sh

# Exponemos el puerto oficial de Hugging Face Spaces
EXPOSE 7860

# Comando final: Ejecutar el script
CMD ["./run.sh"]