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

# Comando padrão (Altere conforme o ponto de entrada da sua aplicação)
CMD ["python", "main.py"]