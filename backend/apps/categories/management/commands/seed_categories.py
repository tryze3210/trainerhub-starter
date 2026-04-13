from django.core.management.base import BaseCommand
from apps.categories.models import Category, Tag


DEFAULT_CATEGORIES = [
    ("zumba", "Zumba"),
    ("bachata", "Bachata"),
    ("stretching", "Stretching"),
    ("strength", "Strength"),
    ("hiit", "HIIT"),
]

DEFAULT_TAGS = [
    ("beginner", "Beginner"),
    ("intermediate", "Intermediate"),
    ("advanced", "Advanced"),
    ("home-workout", "Home Workout"),
]


class Command(BaseCommand):
    help = "Seed default categories and tags"

    def handle(self, *args, **options):
        for slug, name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(slug=slug, defaults={"name": name})
        for slug, name in DEFAULT_TAGS:
            Tag.objects.get_or_create(slug=slug, defaults={"name": name})
        self.stdout.write(self.style.SUCCESS("Seeded categories and tags."))
