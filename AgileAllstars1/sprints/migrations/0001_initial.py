from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('owner_id', models.IntegerField(help_text='References auth.User.id in the auth database')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Sprint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('goal', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('PLANNING', 'Planning'), ('ACTIVE', 'Active'), ('CLOSED', 'Closed')], default='PLANNING', max_length=10)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sprints', to='sprints.project')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BacklogItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('BACKLOG', 'Product Backlog'), ('SPRINT', 'Sprint Backlog'), ('TEST', 'Ready for Test'), ('DONE', 'Complete')], default='BACKLOG', max_length=10)),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MED', 'Medium'), ('HIGH', 'High'), ('CRIT', 'Critical')], default='MED', max_length=5)),
                ('assigned_to_id', models.IntegerField(blank=True, help_text='References auth.User.id in the auth database', null=True)),
                ('created_by_id', models.IntegerField(help_text='References auth.User.id in the auth database')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='backlog_items', to='sprints.project')),
                ('sprint', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='sprints.sprint')),
            ],
            options={
                'ordering': ['-priority', '-updated_at'],
            },
        ),
    ]
