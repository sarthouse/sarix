# SARIX Frontend - Quick Start Guide

## TL;DR - En 3 minutos

```bash
# 1. Setup
cd frontend
npm install
cp .env.example .env.local

# 2. Desarrollo
npm run dev
# Abre http://localhost:5173

# 3. Login
Email: admin@sarix.local
Contraseña: admin123

# 4. Explorar
- Dashboard en ✅
- Navigation (sidebar + navbar) funcional ✅
- Logout button en user menu ✅
```

## Stack Technologies

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Build | Vite | 8.0.4 |
| Runtime | React | 19.2.4 |
| Lenguaje | TypeScript | 6.0.2 |
| Router | React Router | 7.14.0 |
| Styling | Tailwind CSS | 4.2.2 |
| Forms | React Hook Form | 7.72.1 |
| Validation | Zod | 4.3.6 |
| State Query | TanStack Query | 5.99.0 |
| HTTP Client | Axios | 1.15.0 |
| UI Components | shadcn/ui (Radix) | Latest |
| Icons | Lucide React | 1.8.0 |

## Estructura de Carpetas

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Navbar.tsx       # Top bar with user menu
│   │   ├── Sidebar.tsx      # Left nav sidebar
│   │   └── ProtectedRoute.tsx # Route guard wrapper
│   ├── pages/               # Page components (by module)
│   │   ├── auth/            # Auth pages
│   │   │   └── LoginPage.tsx
│   │   └── DashboardPage.tsx
│   ├── layouts/             # Layout wrappers
│   │   └── MainLayout.tsx   # Navbar + Sidebar + Outlet
│   ├── context/             # React Context
│   │   └── AuthContext.tsx  # Auth state (user, tokens, perms)
│   ├── hooks/               # Custom hooks
│   │   └── auth/useAuth.ts  # Auth hook
│   ├── services/            # API calls (TBD Week 2)
│   ├── types/               # TypeScript interfaces
│   │   ├── auth.ts          # Auth types
│   │   └── common.ts        # Common types
│   ├── utils/               # Utilities
│   │   ├── axios.config.ts  # Axios with interceptors
│   │   └── storage.ts       # LocalStorage helpers
│   ├── schemas/             # Zod validation schemas
│   │   └── auth.schema.ts   # Login form validation
│   ├── App.tsx              # Main router
│   └── main.tsx             # Entry point
├── public/                  # Static assets
├── vite.config.ts           # Vite configuration
├── tsconfig.app.json        # TypeScript config
├── SETUP.md                 # Detailed setup guide
└── package.json             # Dependencies
```

## Flujo de Autenticación

```
1. Usuario visita http://localhost:5173
   ↓
2. ProtectedRoute verifica autenticación
   - Si token existe en localStorage → Va a Dashboard
   - Si no → Redirige a /auth/login
   ↓
3. LoginPage muestra formulario
   - Email + Password validados con Zod
   ↓
4. Submit POST /auth/login/
   ↓
5. Backend retorna {access, refresh, user}
   - access → localStorage (corto plazo)
   - refresh → sessionStorage (seguro)
   ↓
6. AuthContext actualiza estado
   ↓
7. Usuario redirigido a /dashboard
   ↓
8. Navbar + Sidebar renderean con user data
   ↓
9. Logout button hace POST /auth/logout/ + clear tokens
```

## Permisos & Roles

Usuarios tienen roles que filtran menú:

```typescript
// En Sidebar, items se filtran:
const items = [
  { label: 'Dashboard', roles: undefined }, // Todos ven
  { label: 'Sales', roles: ['ADMIN', 'SALES', 'MANAGER'] },
  { label: 'Inventory', roles: ['ADMIN', 'INVENTORY', 'MANAGER'] },
  { label: 'Settings', roles: ['ADMIN'] },
];

// En rutas:
<ProtectedRoute requiredRole={['ADMIN']}>
  <AdminPage />
</ProtectedRoute>
```

Roles disponibles:
- `ADMIN` - Acceso a todo
- `MANAGER` - Gerente, manejo de módulos
- `SALES` - Solo ventas
- `PURCHASES` - Solo compras
- `INVENTORY` - Solo inventario
- `ACCOUNTING` - Solo contabilidad
- `VIEWER` - Solo lectura

## API Endpoints

Todos los endpoints están documentados en `schema.yml` (OpenAPI).

Axios automaticamente:
1. Agrega `Authorization: Bearer {token}` a requests
2. Si 401 → auto-intenta refrescar token
3. Si refresh falla → redirige a login

```typescript
// Uso en componentes:
import { api } from '@/utils/axios.config';

const response = await api.get('/sales/orders/');
// Headers + auth mágicamente agregados
```

## Variables de Entorno

```bash
# .env.local
VITE_API_URL=http://localhost:8000/api/v1
```

Por defecto apunta a localhost. Para producción:
```bash
VITE_API_URL=https://api.sarix.com/api/v1
```

## Desarrollo

### Agregar Nueva Página

```typescript
// 1. Crear archivo src/pages/SalesPage.tsx
export const SalesPage = () => {
  const { user } = useAuth();
  
  return (
    <div className="p-6">
      <h1>Sales</h1>
      <p>Hola {user?.firstName}</p>
    </div>
  );
};

// 2. Agregar ruta en App.tsx
<Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
  <Route path="/sales" element={<SalesPage />} />
</Route>

// 3. Sidebar automáticamente muestra si rol permite
```

### Agregar Nuevo Componente

```typescript
// src/components/MyButton.tsx
interface MyButtonProps {
  onClick?: () => void;
  children: React.ReactNode;
}

export const MyButton = ({ onClick, children }: MyButtonProps) => {
  return (
    <button
      onClick={onClick}
      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
    >
      {children}
    </button>
  );
};

// Uso:
import { MyButton } from '@/components/MyButton';
<MyButton onClick={() => console.log('clicked')}>Click me</MyButton>
```

### Agregar Validación Form

```typescript
// 1. Definir schema en src/schemas/sales.schema.ts
import { z } from 'zod';

export const saleOrderSchema = z.object({
  customerEmail: z.string().email('Email inválido'),
  quantity: z.number().min(1, 'Debe ser > 0'),
  totalAmount: z.number().min(0.01),
});

export type SaleOrderFormData = z.infer<typeof saleOrderSchema>;

// 2. Usar en página
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { saleOrderSchema, SaleOrderFormData } from '@/schemas/sales.schema';

export const SalesPage = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<SaleOrderFormData>({
    resolver: zodResolver(saleOrderSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('customerEmail')} />
      {errors.customerEmail && <p>{errors.customerEmail.message}</p>}
    </form>
  );
};
```

## Build & Deploy

### Development
```bash
npm run dev
# http://localhost:5173 con HMR
```

### Production
```bash
npm run build
# Crea dist/ optimizado (50KB gzipped)

npm run preview
# Previsualizar build localmente
```

### Docker (Placeholder para Week 8)
```dockerfile
FROM node:18 AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Testing (Placeholder)

### Unit Tests (TBD Week 8)
```bash
npm run test
```

### E2E Tests (TBD Week 8)
```bash
npm run e2e
```

## Troubleshooting

### Dev server no inicia
```bash
# Verificar puerto 5173 no esté en uso
netstat -tulpn | grep 5173

# O cambiar puerto en vite.config.ts
```

### 401 Unauthorized en requests
```bash
# 1. Verificar que backend está corriendo
curl http://localhost:8000/api/v1/auth/me/ -H "Authorization: Bearer INVALID"
# Debe retornar 401

# 2. Verificar .env.local tiene VITE_API_URL correcto
cat .env.local

# 3. Probar login manual
# Admin: admin@sarix.local / admin123
```

### CORS error
```bash
# Backend debe tener CORS configurado para http://localhost:5173
# En Django: CORS_ALLOWED_ORIGINS = ['http://localhost:5173', ...]
```

### Build falla
```bash
# 1. Limpiar cache
rm -rf node_modules dist .vite

# 2. Reinstalar
npm install

# 3. Intentar build
npm run build
```

### TypeScript errors
```bash
# Verificar tipos
npm run lint

# Fix automáticos
npm run lint -- --fix
```

## Próximas Fases

- **Week 2**: Sales module (CRUD, forms, validation)
- **Week 3**: Purchases module
- **Week 4**: Inventory module
- **Week 5**: Accounting module
- **Week 6**: Reports & charts (Recharts)
- **Week 7**: Partners & localization
- **Week 8**: Polish, testing, mobile

## Links Útiles

- [React 19 Docs](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Docs](https://vitejs.dev)
- [React Router Docs](https://reactrouter.com)
- [Tailwind CSS](https://tailwindcss.com)
- [React Hook Form](https://react-hook-form.com)
- [Zod Validation](https://zod.dev)
- [Axios Docs](https://axios-http.com)

## Contacto & Issues

Si hay problemas:
1. Revisar `frontend/SETUP.md` (guía completa)
2. Revisar console logs en browser (DevTools F12)
3. Revisar network tab (requests/responses)
4. Revisar `schema.yml` para endpoint docs

---

**Happy coding!** 🚀

Próximo paso: Week 2 - Sales Module
