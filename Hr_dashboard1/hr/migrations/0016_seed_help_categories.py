from django.db import migrations
from django.utils.text import slugify

def seed_categories(apps, schema_editor):
    HelpCategory = apps.get_model("hr", "HelpCategory")
    names = ["HR Policy", "Rules", "Guidelines", "Procedures", "FAQ", "Onboarding", "Benefits"]
    for name in names:
        slug = slugify(name)
        HelpCategory.objects.get_or_create(slug=slug, defaults={"name": name})

def unseed_categories(apps, schema_editor):
    HelpCategory = apps.get_model("hr", "HelpCategory")
    slugs = [slugify(n) for n in ["HR Policy", "Rules", "Guidelines", "Procedures", "FAQ", "Onboarding", "Benefits"]]
    HelpCategory.objects.filter(slug__in=slugs).delete()

class Migration(migrations.Migration):
    dependencies = [
        ("hr", "0015_helpcategory_helparticle"),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_code=unseed_categories),
    ]
