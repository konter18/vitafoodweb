# Generated by Django 5.1.3 on 2024-11-15 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ControlUsuarios', '0006_customuser_groups_customuser_user_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(choices=[('supervisor', 'Supervisor'), ('operador', 'Operador'), ('administrador', 'administrador')], default='operador', max_length=20),
        ),
    ]
