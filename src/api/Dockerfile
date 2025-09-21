# src/api/Dockerfile

# Dockerfile básico para o pipeline CI/CD de uma API em Python.
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências
COPY src/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/api/ .

# Variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Porta padrão (pode ser alterada caso necessário)
EXPOSE 8000

# This command is overridden by docker-compose, but it's good practice
# to have a correct default command here.
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000"]