// src/pages/UnauthorizedPage.tsx
import { Link } from 'react-router-dom';
import { Lock, ArrowLeft } from 'lucide-react';

export const UnauthorizedPage = () => {
  return (
    <div className="flex min-h-screen bg-gray-50 items-center justify-center px-4">
      <div className="max-w-md text-center">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
            <Lock className="h-8 w-8 text-red-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Acceso Denegado
          </h1>
          <p className="text-gray-600">
            No tienes permisos para acceder a esta página
          </p>
        </div>

        <p className="text-gray-500 mb-8">
          Si crees que esto es un error, contacta al administrador del sistema.
        </p>

        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver al Dashboard
        </Link>
      </div>
    </div>
  );
};
