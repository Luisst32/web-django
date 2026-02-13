from django.db import migrations

def migrar_imagenes(apps, schema_editor):
    Post = apps.get_model('publications', 'Post')
    PostImagen = apps.get_model('publications', 'PostImagen')

    for post in Post.objects.all():
        if post.imagen:
            PostImagen.objects.create(post=post, imagen=post.imagen, orden=0)

class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0012_postimagen'),
    ]

    operations = [
        migrations.RunPython(migrar_imagenes),
    ]
