# Starting a new database

1. Delete container and volume.
2. `docker-compose up -d`
3. `python manage.py makemigrations account`. This will create a db table for custom user.
4. `python manage.py makemigrations app`. This will create a db table for posts.
5. `python manage.py migrate`


# Recovering comment history

```python
from myapp.models import MyUser, UserEmailHistory

u = MyUser.objects.create(
    username="hello",
    email="hello@hello.com",
    address="123 Main St"
)

# Events are only tracked on updates, so nothing has been stored yet
assert not UserEmailHistory.objects.exists()

# Change the address. An event is not created
u.address = "456 Main St"
u.save()
assert not UserEmailHistory.objects.exists()

# Change the email. An event should be stored
u.email = "world@world.com"
u.save()
# this is the important line
print(UserEmailHistory.objects.filter(pgh_obj=u).values_list("email", flat=True))

> ["hello@hello.com"]
```

Example from [pghistory docs](https://django-pghistory.readthedocs.io/en/3.4.4/event_tracking/#basic-example).