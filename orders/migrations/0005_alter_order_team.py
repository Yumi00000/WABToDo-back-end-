# Generated by Django 5.1 on 2024-12-15 09:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_alter_order_tasks_alter_order_team"),
        ("users", "0004_chat_participant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="team_orders",
                to="users.team",
            ),
        ),
    ]