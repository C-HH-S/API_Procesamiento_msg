# Usar una imagen base oficial de Python
# La versión 'slim' reduce el tamaño de la imagen final
FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requisitos primero para aprovechar el cache de Docker
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente al directorio de trabajo
COPY . .

# Exponer el puerto en el que la aplicación se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# El servidor de desarrollo de Flask se ejecuta en el puerto 5000 por defecto
CMD ["python", "main.py"]