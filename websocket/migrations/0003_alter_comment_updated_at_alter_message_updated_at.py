# Generated by Django 5.1 on 2024-12-14 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("websocket", "0002_message_notification"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="updated_at",
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name="message",
            name="updated_at",
            field=models.DateTimeField(null=True),
        ),
    ]
