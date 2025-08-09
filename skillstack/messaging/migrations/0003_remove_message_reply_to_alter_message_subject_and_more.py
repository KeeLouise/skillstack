from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

operations = [
    migrations.SeparateDatabaseAndState(
        state_operations=[
            migrations.RemoveField(
                model_name='message',
                name='reply_to',
            ),
        ],
        database_operations=[],
    ),

    migrations.AlterField(
        model_name='message',
        name='subject',
        field=models.CharField(max_length=500, blank=True),
    ),

    migrations.SeparateDatabaseAndState(
        state_operations=[
            migrations.CreateModel(
                name='Conversation',
                fields=[
                    ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('created_at', models.DateTimeField(auto_now_add=True)),
                    ('updated_at', models.DateTimeField(auto_now=True)),
                    ('participants', models.ManyToManyField(related_name='conversations', to=settings.AUTH_USER_MODEL)),
                    ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversations', to='projects.project')),
                ],
            ),
        ],
        database_operations=[],
    ),

    migrations.SeparateDatabaseAndState(
        state_operations=[
            migrations.AddField(
                model_name='message',
                name='conversation',
                field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='messaging.conversation'),
            ),
        ],
        database_operations=[],
    ),

    migrations.CreateModel(
        name='MessageAttachment',
        fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('file', models.FileField(upload_to='message_attachments/')),
            ('original_name', models.CharField(max_length=255, blank=True)),
            ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ('message', models.ForeignKey(to='messaging.message', on_delete=django.db.models.deletion.CASCADE, related_name='attachments')),
        ],
    ),
]
