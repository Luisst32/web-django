from django.db import migrations

def seed_terms(apps, schema_editor):
    TermsVersion = apps.get_model('legal', 'TermsVersion')
    TermsVersion.objects.create(
        document_type='full_package',
        language='es',
        version_code='2.1',
        is_active=True,
        content_hash='4e055a001a702626c92c4112b4b199d41aced2f55452d980d7adb609ae803201'
    )
    TermsVersion.objects.create(
        document_type='full_package',
        language='en',
        version_code='2.1',
        is_active=True,
        content_hash='c3717241d6a1b71871dc28b406dc74cc79316cbca352666d90dcdda8c5c79527'
    )

class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_terms),
    ]
