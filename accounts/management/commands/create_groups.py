from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


GROUPS_PERMISSIONS = {
    "moderator": ("change_post", "delete_post", "change_comment", "delete_comment",),
}


class Command(BaseCommand):
    help = 'Creates groups and assigns permissions'

    def handle(self, *args, **options):
        for group, permissions in GROUPS_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name='moderator')
            if not created:
                raise ValueError(f"Group '{group}' already exists")
            for permission in permissions:
                p = Permission.objects.get(codename=permission)
                group.permissions.add(p)
