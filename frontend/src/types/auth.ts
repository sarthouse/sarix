// src/types/auth.ts
export type UserRole = 'ADMIN' | 'MANAGER' | 'SALES' | 'PURCHASES' | 'INVENTORY' | 'ACCOUNTING' | 'VIEWER';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  permissions: string[];
  company: {
    id: string;
    name: string;
  };
  avatar?: string;
  lastLogin?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface TokenPayload {
  sub: string;
  email: string;
  exp: number;
  iat: number;
}
