#!/usr/bin/env python3
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from django.contrib.auth.models import User

admin_username = 'admin'
admin_password = 'admin'

# Delete existing admin if any
User.objects.filter(username=admin_username).delete()

# Create fresh admin user
admin_user = User.objects.create_superuser(
    username=admin_username,
    email='admin@example.com',
    password=admin_password
)

print(f"✅ Admin user created/reset")
print(f"   Username: {admin_username}")
print(f"   Password: {admin_password}")
print(f"   Is superuser: {admin_user.is_superuser}")
print(f"   Is staff: {admin_user.is_staff}")
