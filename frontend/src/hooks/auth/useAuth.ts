// src/hooks/auth/useAuth.ts
import { useCallback } from 'react';
import { useAuthContext } from '@/context/AuthContext';
import { api } from '@/utils/axios.config';
import { AuthStorage } from '@/utils/storage';
import { User, LoginRequest } from '@/types/auth';

export const useAuth = () => {
  const { user, isLoading, isAuthenticated, setUser, hasPermission, hasRole, hasAnyPermission } = useAuthContext();

  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      const response = await api.post('/auth/login/', credentials);
      const { access, refresh, user: userData } = response.data;
      
      AuthStorage.setTokens(access, refresh);
      AuthStorage.setUser(userData);
      setUser(userData);
      
      return userData;
    } catch (error) {
      throw error;
    }
  }, [setUser]);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      AuthStorage.clearTokens();
      setUser(null);
      window.location.href = '/auth/login';
    }
  }, [setUser]);

  const refreshUser = useCallback(async () => {
    try {
      const response = await api.get('/auth/me/');
      const userData: User = response.data;
      AuthStorage.setUser(userData);
      setUser(userData);
      return userData;
    } catch (error) {
      AuthStorage.clearTokens();
      setUser(null);
      throw error;
    }
  }, [setUser]);

  return {
    user,
    isLoading,
    isAuthenticated,
    hasPermission,
    hasRole,
    hasAnyPermission,
    login,
    logout,
    refreshUser,
  };
};
