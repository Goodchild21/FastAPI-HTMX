FROM python:3.11-alpine

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

# RUN pip freeze > requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Открываем порт
EXPOSE 8000

# Запускаем сервер FastAPI
CMD ["uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]

# FROM python:3.12-slim
#
# ENV PYTHONUNBUFFERED 1
#
# RUN addgroup --system fastapi \
#     && adduser --system --ingroup fastapi fastapi
#
# COPY --chown=fastapi:fastapi ./requirements.txt /requirements.txt
# RUN pip freeze > requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
#
# COPY --chown=fastapi:fastapi ./start /start
# RUN sed -i 's/\r$//g' /start
# RUN chmod +x /start

# COPY --chown=fastapi:fastapi . /app
#
# WORKDIR /app