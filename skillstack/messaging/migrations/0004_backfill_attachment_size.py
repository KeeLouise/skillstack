from django.db import migrations
from django.core.files.storage import default_storage

def backfill_sizes(apps, schema_editor):
    Attachment = apps.get_model('messaging', 'MessageAttachment')
    for a in Attachment.objects.filter(size__isnull=True).iterator():
        try:
            s = default_storage.size(a.file.name)
        except Exception:
            s = None
        a.size = s
        a.save(update_fields=['size'])

class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0003_your_previous_migration_name'),
    ]

    operations = [
        migrations.RunPython(backfill_sizes, migrations.RunPython.noop),
    ]