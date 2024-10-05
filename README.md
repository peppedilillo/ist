# Starting a new database

1. Delete container and volume.
2. `docker-compose up -d`
3. `python manage.py makemigrations account`. This will create a db table for custom user.
4. `python manage.py makemigrations app`. This will create a db table for posts.
5. `python manage.py migrate`

