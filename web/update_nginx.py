import sys
import re

filepath = '/etc/nginx/sites-available/django'

try:
    with open(filepath, 'r') as f:
        content = f.read()
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

# Clean up any existing client_max_body_size definitions in the file
content = re.sub(r'\s*client_max_body_size\s+[^;]+;', '', content)

target_str = 'ssl_ciphers HIGH:!aNULL:!MD5;'
replacement_str = 'ssl_ciphers HIGH:!aNULL:!MD5;\n\n    client_max_body_size 500M;'

if target_str in content:
    new_content = content.replace(target_str, replacement_str)
    with open(filepath, 'w') as f:
        f.write(new_content)
    print("Nginx configuration updated successfully to 500M.")
else:
    print("Target pattern not found in Nginx configuration.")
    sys.exit(1)
