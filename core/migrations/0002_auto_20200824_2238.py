# Generated by Django 2.2 on 2020-08-24 22:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contestgroup',
            name='name',
            field=models.TextField(help_text='contest group name'),
        ),
        migrations.AlterUniqueTogether(
            name='contestgroup',
            unique_together={('name', 'type')},
        ),
        migrations.AlterUniqueTogether(
            name='wordcontest',
            unique_together={('spellbee_type', 'phase', 'contest')},
        ),
    ]