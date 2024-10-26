from django.db import migrations
from ..models import Board, Keyword


def create_initial_data(apps, schema_editor):
    for choice in Board.Boards:
        Board.objects.get_or_create(name=choice.value)
    for choice in Keyword.Keywords:
        Keyword.objects.get_or_create(name=choice.value)


def reverse_initial_data(apps, schema_editor):
    Board = apps.get_model("app", "Board")
    Keyword = apps.get_model("app", "Keyword")
    Board.objects.all().delete()
    Keyword.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_initial_data, reverse_initial_data),
    ]
