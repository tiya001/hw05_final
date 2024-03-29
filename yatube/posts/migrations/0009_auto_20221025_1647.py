# Generated by Django 2.2.16 on 2022-10-25 13:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_auto_20221025_1643'),
    ]

    operations = [
        migrations.AlterField(
            model_name='follow',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='following', to=settings.AUTH_USER_MODEL, verbose_name='автор'),
        ),
        migrations.AlterField(
            model_name='follow',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='follower', to=settings.AUTH_USER_MODEL, verbose_name='подписчик'),
        ),
    ]
