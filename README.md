1. Убедитесь, что установлен Docker
2. Клонируйте репозиторий с проектом
bash
git clone <https://github.com/mrgafurov2016/REST-API>

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
