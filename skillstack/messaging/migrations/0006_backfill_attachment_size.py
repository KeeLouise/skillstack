from django.db import migrations, models

def backfill_sizes(apps, schema_editor):
    MessageAttachment = apps.get_model('messaging', 'MessageAttachment')

    qs = MessageAttachment.objects.filter(models.Q(size__isnull=True) | models.Q(size=0))

    for a in qs.iterator(chunk_size=2000):
        file_size = None
        try:
            if a.file: 
                file_size = a.file.size
        except Exception:
            file_size = None

        if file_size is not None:
            a.size = file_size
            a.save(update_fields=['size'])

class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0005_add_attachment_size'),
    ]

    operations = [
        migrations.RunPython(backfill_sizes, migrations.RunPython.noop),
    ]