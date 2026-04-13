// src/components/Sidebar.tsx
import { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/auth/useAuth';
import {
  BarChart3,
  ShoppingCart,
  Package,
  DollarSign,
  Users,
  Settings,
  FileText,
  TrendingUp,
  X,
} from 'lucide-react';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar = ({ isOpen = true, onClose }: SidebarProps) => {
  const location = useLocation();
  const { hasPermission, hasRole, user } = useAuth();

  // Definir menú con permisos
  const menuItems = useMemo(() => {
    const items: Array<{
      label: string;
      href: string;
      icon: React.ReactNode;
      permissions?: string[];
      roles?: string[];
    }> = [
      {
        label: 'Dashboard',
        href: '/dashboard',
        icon: <BarChart3 className="h-5 w-5" />,
      },
      {
        label: 'Ventas',
        href: '/sales',
        icon: <ShoppingCart className="h-5 w-5" />,
        roles: ['ADMIN', 'SALES', 'MANAGER'],
      },
      {
        label: 'Compras',
        href: '/purchases',
        icon: <Package className="h-5 w-5" />,
        roles: ['ADMIN', 'PURCHASES', 'MANAGER'],
      },
      {
        label: 'Inventario',
        href: '/inventory',
        icon: <Package className="h-5 w-5" />,
        roles: ['ADMIN', 'INVENTORY', 'MANAGER'],
      },
      {
        label: 'Contabilidad',
        href: '/accounting',
        icon: <DollarSign className="h-5 w-5" />,
        roles: ['ADMIN', 'ACCOUNTING', 'MANAGER'],
      },
      {
        label: 'Pagos',
        href: '/payments',
        icon: <TrendingUp className="h-5 w-5" />,
        roles: ['ADMIN', 'MANAGER'],
      },
      {
        label: 'Reportes',
        href: '/reports',
        icon: <FileText className="h-5 w-5" />,
        roles: ['ADMIN', 'MANAGER', 'VIEWER'],
      },
      {
        label: 'Socios',
        href: '/partners',
        icon: <Users className="h-5 w-5" />,
        roles: ['ADMIN', 'MANAGER'],
      },
      {
        label: 'Configuración',
        href: '/settings',
        icon: <Settings className="h-5 w-5" />,
        roles: ['ADMIN'],
      },
    ];

    return items.filter((item) => {
      if (item.roles) {
        return item.roles.some((role) => hasRole(role as any));
      }
      if (item.permissions) {
        return item.permissions.some((perm) => hasPermission(perm));
      }
      return true;
    });
  }, [hasPermission, hasRole]);

  const isActive = (href: string) => {
    return location.pathname === href || location.pathname.startsWith(href + '/');
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 lg:hidden z-30"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-gray-900 text-white transition-transform duration-300 lg:translate-x-0 pt-16 lg:pt-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Close Button (Mobile) */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 lg:hidden p-2 hover:bg-gray-800 rounded-lg"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Content */}
        <div className="h-full flex flex-col overflow-y-auto">
          {/* Logo (Mobile) */}
          <div className="lg:hidden px-6 py-4 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-lg flex items-center justify-center font-bold text-sm">
                S
              </div>
              <span className="font-bold text-lg">SARIX</span>
            </div>
          </div>

          {/* Menu Items */}
          <nav className="flex-1 px-3 py-6 space-y-2">
            {menuItems.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                  isActive(item.href)
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                {item.icon}
                <span className="text-sm font-medium">{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Footer */}
          <div className="px-3 py-4 border-t border-gray-800">
            <div className="px-4 py-3 bg-gray-800 rounded-lg">
              <p className="text-xs text-gray-400 mb-2">Conectado como</p>
              <p className="text-sm font-medium truncate">
                {user?.firstName} {user?.lastName}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
