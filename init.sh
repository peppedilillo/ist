docker-compose up -d
python manage.py makemigrations accounts
python manage.py makemigrations app
python manage.py makemigrations demo
python manage.py migrate
python manage.py createsuperuser