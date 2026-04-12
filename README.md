# SARIX — Sistema Contable API

Sistema contable profesional basado en la metodología de partida doble, diseñado para empresas que necesitan gestionar su contabilidad de manera eficiente y automatizada.

## Características Principales

### 📊 Contabilidad Completa
- **Plan de cuentas jerárquico** — Estructura tipo RT9 con niveles ilimitados (MPTT)
- **Partida doble** — Validación automática de balance (total debe = total haber)
- **Asientos contables** — Crear, modificar, contabilizar y anular
- **Períodos fiscales** — Gestión de ejercicios y períodos contables con cierre

### 🔄 Automatización
- **Auto-numeración** — Generación automática de números de asiento (YYYY-NNNNNN)
- **Cache de reportes** — Invalidación automática al contabilizar
- **Tareas asíncronas** — Celery para procesos pesados (reportes, exports)
- **Señales** — Invalidación de cache en tiempo real

### 📈 Reportes
- **Balance de saldos** — Activo, Pasivo, Patrimonio a fecha determinada
- **Estado de resultados (P&L)** — Ingresos, Egresos y resultado neto
- **Libro mayor** — Movimientos por cuenta con saldo acumulado

### 🔐 Seguridad
- **JWT Authentication** — Tokens de acceso y refresh
- **Permisos por vista** — Control de acceso granular
- **Validaciones** — Períodos cerrados, cuentas sin movimientos, balanceo

### 🏗️ Arquitectura
- **Multi-instancia** — Un repositorio, una instancia por cliente
- **API RESTful** — Integración con cualquier frontend
- **Docker** — Contenedores listos para producción
- **Documentación Swagger** — Explorador interactivo de API

## Tecnologías

| Categoría | Tecnología |
|-----------|-------------|
| Framework | Django 6.0 + DRF |
| Base de datos | PostgreSQL 16 |
| Cache/Cola | Redis 7 |
| Tareas | Celery + Beat |
| API Docs | DRF Spectacular |
| Plantillas | DRF YASG |

## Estructura del Proyecto

```
sarix/
├── apps/                    # Aplicaciones Django
│   ├── company/            # Datos de la empresa
│   ├── accounts/            # Plan de cuentas (MPTT)
│   ├── partners/           # Clientes y proveedores
│   ├── periods/            # Ejercicios y períodos
│   ├── accounting/         # Asientos contables
│   └── reports/            # Reportes contables
├── core/                    # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   └── exceptions.py
├── docker-compose.yml      # Servicios Docker
├── Dockerfile              # Imagen de la app
├── nginx.conf              # Configuración Nginx
└── requirements.txt        # Dependencias Python
```

## Primeros Pasos

### 1. Levantar el Sistema

Con Docker:
```bash
rav run docker-up
```

Sin Docker (desarrollo):
```bash
# Activar venv
source venv/bin/activate

# Migraciones
python manage.py migrate

# Crear superuser
python manage.py createsuperuser

# Ejecutar servidor
python manage.py runserver
```

### 2. Configuración Inicial

Una vez levantado, ejecutar en orden:

```bash
# 1. Importar plan de cuentas
docker compose exec api python manage.py seed_accounts --file=utils/plan_cuentas.csv

# 2. Crear empresa
docker compose exec api python manage.py shell -c "
from apps.company.models import Company
Company.objects.create(name='Mi Empresa SA', cuit='30-12345678-9', currency='ARS')
"

# 3. Crear ejercicio fiscal
docker compose exec api python manage.py shell -c "
from apps.periods.models import FiscalYear, AccountingPeriod
fy = FiscalYear.objects.create(name='2026', start_date='2026-01-01', end_date='2026-12-31')
AccountingPeriod.objects.create(fiscal_year=fy, name='Enero', start_date='2026-01-01', end_date='2026-01-31')
"
```

### 3. Obtener Token JWT

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password"}'
```

Respuesta:
```json
{
  "access": "eyJ0eXAiOiJKV1Q...",
  "refresh": "eyJ0eXAiOiJKV1Q..."
}
```

### 4. Usar la API

Agregar el token en los headers:
```bash
curl http://localhost:8000/api/v1/accounts/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..."
```

## Endpoints Principales

### Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/token/` | Obtener access token |
| POST | `/api/v1/auth/token/refresh/` | Renovar access token |

### Empresa

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/company/` | Ver datos de empresa |
| PUT | `/api/v1/company/` | Actualizar datos |

### Plan de Cuentas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/accounts/` | Listar cuentas activas |
| POST | `/api/v1/accounts/` | Crear cuenta |
| GET | `/api/v1/accounts/tree/` | Ver árbol completo |
| GET | `/api/v1/accounts/{id}/` | Ver cuenta específica |
| PUT | `/api/v1/accounts/{id}/` | Actualizar cuenta |
| DELETE | `/api/v1/accounts/{id}/` | Desactivar cuenta |

### Terceros (Partners)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/partners/` | Listar terceros |
| POST | `/api/v1/partners/` | Crear tercero |
| GET | `/api/v1/partners/{id}/` | Ver tercero |
| PUT | `/api/v1/partners/{id}/` | Actualizar tercero |
| DELETE | `/api/v1/partners/{id}/` | Eliminar tercero |

### Asientos Contables (Journals)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/journals/` | Listar asientos |
| POST | `/api/v1/journals/` | Crear asiento (borrador) |
| GET | `/api/v1/journals/{id}/` | Ver asiento completo |
| PUT | `/api/v1/journals/{id}/` | Actualizar asiento |
| POST | `/api/v1/journals/{id}/post_journal/` | Contabiliza el asiento |
| POST | `/api/v1/journals/{id}/cancel/` | Anula y crea reversa |

### Reportes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/reports/balance/?date=YYYY-MM-DD` | Balance de saldos |
| GET | `/api/v1/reports/profit-loss/?period=1` | Estado de resultados |
| GET | `/api/v1/reports/general-ledger/?account=5` | Libro mayor |

### Documentación

| Endpoint | Descripción |
|----------|-------------|
| `/api/schema/swagger/` | Swagger UI (visual) |
| `/api/schema/` | Spec JSON |

## Ejemplos de Uso

### Crear un Asiento Contable

```bash
curl -X POST http://localhost:8000/api/v1/journals/ \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-01-15",
    "description": "Venta del día",
    "period": 1,
    "lines": [
      {"account": 15, "debit_amount": 12100.00, "credit_amount": 0},
      {"account": 45, "debit_amount": 0, "credit_amount": 12100.00}
    ]
  }'
```

### Contabilizar un Asiento

```bash
curl -X POST http://localhost:8000/api/v1/journals/1/post_journal/ \
  -H "Authorization: Bearer TU_TOKEN"
```

### Obtener Balance

```bash
curl "http://localhost:8000/api/v1/reports/balance/?date=2026-01-31" \
  -H "Authorization: Bearer TU_TOKEN"
```

## Servicios Docker

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| API | 8000 | Aplicación Django |
| Nginx | 80 | Proxy reverso |
| PostgreSQL | 5432 | Base de datos |
| Redis | 6379 | Cache y cola |
| Flower | 5555 | Monitor Celery (admin/admin) |
| Celery Worker | - | Procesa tareas |
| Celery Beat | - | Programador de tareas |

## Comandos Útiles

```bash
# Ver logs
rav run docker-logs

# Reiniciar servicios
rav run docker-restart

# Detener servicios
rav run docker-down

# Crear migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Importar plan de cuentas
python manage.py seed_accounts --file=utils/plan_cuentas.csv
```

## Configuración de Variables

Crear archivo `.env`:

```bash
SECRET_KEY=tu-secret-key-de-50-caracteres-minimo
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=contabilidad
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

## Licencia

MIT License