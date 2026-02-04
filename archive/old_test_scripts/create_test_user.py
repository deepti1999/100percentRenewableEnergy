#!/usr/bin/env python
"""
Create a test user for accessing the webapp
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

from django.contrib.auth.models import User

print()
print('='*80)
print('CHECKING/CREATING TEST USER')
print('='*80)
print()

# Check if any users exist
user_count = User.objects.count()
print(f'Total users in database: {user_count}')

if user_count > 0:
    print('\nExisting users:')
    for user in User.objects.all():
        print(f'  - Username: {user.username}')
        print(f'    Email: {user.email}')
        print(f'    Superuser: {user.is_superuser}')
        print(f'    Active: {user.is_active}')
        print()
else:
    print('\nNo users found. Creating test user...')
    print()
    
    # Create a test user
    username = 'testuser'
    password = 'testpass123'
    email = 'test@example.com'
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    print('✅ Test user created successfully!')
    print()
    print('Login credentials:')
    print(f'  Username: {username}')
    print(f'  Password: {password}')
    print()
    print('You can now login at: http://localhost:8000/login/')
    print()

print('='*80)
print('To access the renewable data page:')
print('  1. Start server: python manage.py runserver')
print('  2. Go to: http://localhost:8000/')
print('  3. Login with your credentials')
print('  4. Navigate to renewable data or landuse pages')
print('='*80)
print()
