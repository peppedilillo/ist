docker-compose up -d
python manage.py makemigrations accounts
python manage.py makemigrations app
python manage.py migrate
