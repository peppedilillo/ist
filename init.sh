docker-compose up -d
echo "[1/3] Running migrations"
python manage.py makemigrations accounts
python manage.py makemigrations app
python manage.py makemigrations demo
python manage.py migrate
echo "[2/3] Crating superuser.."
python manage.py createsuperuser
