// src/pages/DashboardPage.tsx
import { useAuth } from '@/hooks/auth/useAuth';
import { BarChart3, Users, Package, DollarSign } from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();

  const stats = [
    {
      label: 'Ventas Totales',
      value: '$12,450',
      icon: <DollarSign className="h-6 w-6" />,
      color: 'bg-blue-500',
    },
    {
      label: 'Productos',
      value: '248',
      icon: <Package className="h-6 w-6" />,
      color: 'bg-green-500',
    },
    {
      label: 'Clientes',
      value: '42',
      icon: <Users className="h-6 w-6" />,
      color: 'bg-purple-500',
    },
    {
      label: 'Ingresos',
      value: '+12.5%',
      icon: <BarChart3 className="h-6 w-6" />,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="p-6 lg:p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Bienvenido, {user?.firstName}
        </h1>
        <p className="text-gray-600 mt-2">
          Aquí está el resumen de tu negocio
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">{stat.label}</h3>
              <div className={`${stat.color} p-3 rounded-lg text-white`}>
                {stat.icon}
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Content Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">
            Actividad Reciente
          </h2>
          <div className="space-y-4">
            {[1, 2, 3].map((idx) => (
              <div
                key={idx}
                className="flex items-center gap-4 pb-4 border-b border-gray-100 last:border-b-0"
              >
                <div className="h-10 w-10 bg-gray-200 rounded-full flex-shrink-0"></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    Venta completada #{idx}
                  </p>
                  <p className="text-xs text-gray-500">Hace 2 horas</p>
                </div>
                <p className="text-sm font-semibold text-green-600">+$500</p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">
            Accesos Rápidos
          </h2>
          <div className="space-y-2">
            <a
              href="/sales"
              className="block px-4 py-2 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-sm font-medium transition"
            >
              Nueva Venta
            </a>
            <a
              href="/purchases"
              className="block px-4 py-2 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 text-sm font-medium transition"
            >
              Nueva Compra
            </a>
            <a
              href="/inventory"
              className="block px-4 py-2 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 text-sm font-medium transition"
            >
              Ver Inventario
            </a>
            <a
              href="/reports"
              className="block px-4 py-2 rounded-lg bg-orange-50 text-orange-700 hover:bg-orange-100 text-sm font-medium transition"
            >
              Reportes
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
