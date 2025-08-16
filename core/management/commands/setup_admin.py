from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Create default admin user with username "admin" and password "admin123"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if admin user already exists',
        )

    def handle(self, *args, **options):
        username = 'admin'
        password = 'admin123'
        email = 'admin@msmenergyerp.com'
        
        try:
            with transaction.atomic():
                # Check if admin user already exists
                if User.objects.filter(username=username).exists():
                    if options['force']:
                        # Delete existing admin user
                        User.objects.filter(username=username).delete()
                        self.stdout.write(
                            self.style.WARNING(f'Existing admin user "{username}" deleted.')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Admin user "{username}" already exists. '
                                'Use --force to recreate.'
                            )
                        )
                        return
                
                # Create the admin user
                admin_user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name='System',
                    last_name='Administrator'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created admin user "{username}" with password "{password}"'
                    )
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        'You can now login to the admin panel at /admin/ with these credentials.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {str(e)}')
            )
            raise