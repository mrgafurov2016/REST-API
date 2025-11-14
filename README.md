1. Убедитесь, что установлен Docker
2. Клонируйте репозиторий с проектом
bash
git clone <ссылка_на_репозиторий>
cd <папка_проекта>
Если просто файл — положите его в отдельную папку.
3. Проверьте наличие Dockerfile

В корне проекта должен лежать файл **Dockerfile**. Пример:
```dockerfile
FROM python:3.11

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

4. Соберите Docker-образ

bash
docker build -t myapp .

5. Запустите контейнер

bash
docker run -p 8000:8000 myapp

6. Проверьте работу API

Откройте браузер и перейдите по адресу:
http://localhost:8000/docs
или  
http://localhost:8000/redoc
— откроется Swagger UI или Redoc с документацией.

Готово!

API будет доступно на `localhost:8000`.  
Можно тестировать методы, смотреть документацию и работать с сервисом.
