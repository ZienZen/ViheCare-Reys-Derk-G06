from django.db import migrations

TYPES = [
    'Oil Change',
    'Brake Pads',
    'Brake Fluid',
    'Tire Rotation',
    'Tire Replacement',
    'Battery Check',
    'Air Filter',
    'Coolant Flush',
    'Spark Plugs',
    'Chain and Sprocket',
    'Transmission Service',
    'General Check-up',
    'Other',
]


def seed(apps, schema_editor):
    MaintenanceType = apps.get_model('maintenance', 'MaintenanceType')
    for name in TYPES:
        MaintenanceType.objects.get_or_create(type_name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('maintenance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
