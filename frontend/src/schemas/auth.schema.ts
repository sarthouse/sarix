// src/schemas/auth.schema.ts
import { z } from 'zod';

export const loginSchema = z.object({
  email: z
    .string()
    .email('Email inválido')
    .min(1, 'Email es requerido'),
  password: z
    .string()
    .min(6, 'Contraseña debe tener al menos 6 caracteres')
    .min(1, 'Contraseña es requerida'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
