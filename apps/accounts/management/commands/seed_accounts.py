import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.accounts.models import Account

class Command(BaseCommand):
    help = 'Importa el plan de cuentas desde CSV. Uso: python manage.py seed_accounts --file=/path/to/file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            '-f',
            type=str,
            required=True,
            help='Ruta al archivo CSV del plan de cuentas'
        )

    def handle(self, *args, **options):
        csv_path = Path(options['file'])
        
        if not csv_path.exists():
            raise CommandError(f'Archivo no encontrado {csv_path}')
        
        accounts_created = 0
        accounts_updated = 0

        # Leer y ordenar CSV (por número de puntos para crear padres primero)
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Ordenar: primero los que tienen menos segmentos en el código
        rows.sort(key=lambda r: (r['code'].count('.'), r['code']))

        # Crear mapa de cuentas por código para resolver parents
        accounts_map = {}

        for row in rows:
            code = row['code'].strip()
            name = row['name'].strip()
            account_type = row['account_type'].strip()
            allows_movements = bool(int(row.get('allows_movements', 0)))
            parent_code = row.get('parent_code', '').strip()

            # Buscar parent
            parent = None
            if parent_code and parent_code in accounts_map:
                parent = accounts_map[parent_code]
            
            # Crear o actualizar cuenta
            account, created = Account.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'account_type': account_type,
                    'allows_movements': allows_movements,
                    'parent': parent,
                }
            )
            accounts_map[code] = account
            if created:
                accounts_created += 1
            else:
                accounts_updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Plan de cuentas importado: {accounts_created} creadas, {accounts_updated} actualizadas'
        ))