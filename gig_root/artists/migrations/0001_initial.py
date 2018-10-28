# Generated by Django 2.1.2 on 2018-10-28 15:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArtistModel',
            fields=[
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('stage_name', models.CharField(max_length=30, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('profile_pic', models.CharField(max_length=50)),
                ('background_pic', models.CharField(max_length=50)),
                ('biography', models.TextField(null=True)),
                ('instruments', models.TextField(null=True)),
                ('genres', models.TextField(null=True)),
                ('idols', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='BandModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='artistmodel',
            name='bands',
            field=models.ManyToManyField(to='artists.BandModel'),
        ),
    ]
