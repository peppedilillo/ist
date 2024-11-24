echo "[1/3] Running migrations.."
python manage.py makemigrations accounts
python manage.py makemigrations mboard
python manage.py migrate
echo "[2/3] Creating superuser.."
python manage.py createsuperuser
echo "[3/3] Creating keywords and boards.."
python manage.py createkeywords
python manage.py createboards