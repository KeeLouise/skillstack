from django.db import migrations, models

def backfill_sizes(apps, schema_editor):
    MessageAttachment = apps.get_model('messaging', 'MessageAttachment')
    qs = MessageAttachment.objects.filter(models.Q(size__isnull=True) | models.Q(size=0))
    for a in qs.iterator(chunk_size=2000):
        try:
            s = a.file.size if a.file else None
        except Exception:
            s = None
        if s is not None:
            a.size = s
            a.save(update_fields=['size'])

class Migration(migrations.Migration):
    dependencies = [
        ('messaging', '0004_add_attachment_size'),
    ]
    operations = [
        migrations.RunPython(backfill_sizes, migrations.RunPython.noop),
    ]
