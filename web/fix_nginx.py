import os
import sys
import subprocess

filepath = '/etc/nginx/sites-available/django'

try:
    with open(filepath, 'r') as f:
        content = f.read()
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

if "location /media/" in content:
    print("Media location already exists.")
    sys.exit(0)

# We want to insert the media location right before 'location / {'
media_block = """
    location /media/ {
        alias /home/ubuntu/web-django/web/media/;
        access_log off;
        expires max;
    }

    location /static/ {
        alias /home/ubuntu/web-django/web/staticfiles/;
        access_log off;
        expires max;
    }

    location / {
"""

if "location / {" in content:
    new_content = content.replace("location / {", media_block)
    with open("temp_nginx.conf", "w") as f:
        f.write(new_content)
    
    # We will need sudo to copy it over
    print("Run: sudo cp temp_nginx.conf /etc/nginx/sites-available/django && sudo systemctl reload nginx")
else:
    print("Could not find 'location / {' in the config")
