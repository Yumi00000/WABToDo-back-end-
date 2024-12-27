from django.core.management.base import BaseCommand
from users.models import CustomAuthToken
from django.utils.timezone import now


class Command(BaseCommand):
    help = "Deletes expired tokens."

    def handle(self, *args, **kwargs):
        expired_tokens = CustomAuthToken.objects.filter(expires_at__lte=now())
        count = expired_tokens.count()
        expired_tokens.delete()
        self.stdout.write(f"{count} expired tokens removed.")
