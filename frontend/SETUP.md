# SARIX Frontend - Guía de Setup

## Requisitos Previos

- Node.js 18+ instalado
- Backend SARIX ejecutándose en `http://localhost:8000`

## Instalación

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar variables de entorno
cp .env.example .env.local
# Editar .env.local si es necesario (por defecto apunta a http://localhost:8000/api/v1)
```

## Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# El frontend estará disponible en http://localhost:5173
```

## Build para Producción

```bash
# Compilar y crear bundle optimizado
npm run build

# Previsualizar build localmente
npm preview
```

## Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   ├── Navbar.tsx      # Barra superior con user menu
│   ├── Sidebar.tsx     # Menú lateral de navegación
│   └── ProtectedRoute.tsx  # Envoltorio para rutas protegidas
├── pages/              # Páginas (por módulo)
│   ├── auth/           # Páginas de autenticación
│   └── DashboardPage.tsx
├── layouts/            # Layouts principales
│   └── MainLayout.tsx  # Layout con Navbar + Sidebar
├── context/            # React Context
│   └── AuthContext.tsx # Estado global de autenticación
├── hooks/              # Custom hooks
│   └── auth/useAuth.ts # Hook para usar auth
├── services/           # API calls (por módulo)
├── types/              # TypeScript interfaces
├── utils/              # Funciones auxiliares
│   ├── axios.config.ts # Axios cliente con interceptores
│   └── storage.ts      # LocalStorage helpers
├── schemas/            # Validación Zod
└── App.tsx             # Router principal
```

## Autenticación

### Flujo de Login

1. Usuario accede a `/auth/login`
2. Completa email + contraseña
3. Backend retorna `access_token` y `refresh_token`
4. Tokens se guardan en: 
   - Access: `localStorage` (corta duración)
   - Refresh: `sessionStorage` (larga duración)
5. Usuario redirigido a `/dashboard`

### Interceptores de Axios

- **Request**: Agrega `Authorization: Bearer {token}` a todas las requests
- **Response**: Si recibe 401, intenta renovar token automáticamente
  - Cola las requests fallidas
  - Hace POST a `/auth/refresh/`
  - Re-intenta requests originales con nuevo token
  - Si refresh falla, redirige a login

### Permisos y Roles

El hook `useAuth()` proporciona:

```typescript
const { 
  user,              // Usuario actual (null si no autenticado)
  isAuthenticated,   // Boolean
  isLoading,         // Boolean (cargando datos iniciales)
  hasRole,           // (role: string) => boolean
  hasPermission,     // (permission: string) => boolean
  hasAnyPermission,  // (permissions: string[]) => boolean
  login,             // (credentials) => Promise<User>
  logout,            // () => Promise<void>
  refreshUser,       // () => Promise<User>
} = useAuth();
```

### Proteger Rutas

```tsx
<Route
  element={
    <ProtectedRoute requiredRole={['ADMIN']}>
      <AdminPage />
    </ProtectedRoute>
  }
/>
```

## Variables de Entorno

```bash
# .env.local
VITE_API_URL=http://localhost:8000/api/v1
```

## Credenciales de Demo

Para testing local con backend de desarrollo:

- **Email**: admin@sarix.local
- **Contraseña**: admin123

## Tecnologías Utilizadas

- **React 19** - Framework UI
- **TypeScript 6** - Type safety
- **Vite 8** - Build tool
- **TanStack Query** - Server state management (pendiente Week 2)
- **React Hook Form** - Form management
- **Zod** - Schema validation
- **Tailwind CSS 4** - Styling
- **React Router 7** - Navigation
- **Axios** - HTTP client
- **Lucide React** - Icons

## Próximas Fases

### Week 2: Sales Module
- Sales Orders CRUD
- Sales Quotes
- Customer management
- Order status tracking

### Week 3: Purchases Module
- Purchase Orders CRUD
- Supplier management
- PO approval workflow

### Week 4: Inventory Module
- Stock management
- Stock movements
- Warehouse operations
- Low stock alerts

### Week 5: Accounting Module
- Journals & Entries
- Account ledger
- Charts of accounts

### Week 6: Reports & Charts
- Sales reports
- Inventory reports
- Financial dashboards
- Export to Excel

### Week 7: Partners & Localization
- Customer management
- Supplier management
- Multi-language support
- Regional settings

### Week 8: Polish & Testing
- Performance optimization
- E2E testing
- Mobile responsiveness
- Bug fixes

## Comandos Útiles

```bash
# Linter + formatter
npm run lint

# Type checking
npm run tsc

# Build production
npm run build

# Preview production build
npm run preview
```

## Troubleshooting

### "Cannot find module '@/...'"
- Verificar que `tsconfig.app.json` tiene `baseUrl` y `paths` correctos
- Verificar que `vite.config.ts` tiene `alias` configurado

### "401 Unauthorized" al hacer requests
- Verificar que backend está corriendo en `VITE_API_URL`
- Verificar credenciales de login
- Revisar que tokens se guardan correctamente en storage

### "CORS error"
- Backend debe tener `CORS_ALLOWED_ORIGINS` que incluya `http://localhost:5173`
- Verificar `vite.config.ts` server.proxy configuration

### Build falla
- Limpiar: `rm -rf node_modules dist .vite`
- Reinstalar: `npm install`
- Intentar build nuevamente: `npm run build`

## Links Útiles

- [React 19 Docs](https://react.dev)
- [Vite Docs](https://vite.dev)
- [React Router Docs](https://reactrouter.com)
- [TailwindCSS Docs](https://tailwindcss.com)
- [OpenAPI Schema](../schema.yml)
