from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('messaging', '0006_message_archived_message_deleted_by_recipient_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]
