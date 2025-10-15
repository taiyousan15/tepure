/**
 * Authentication utility functions
 */

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

export interface User {
  id: string;
  email: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
  user: User;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

/**
 * Store authentication token in localStorage
 */
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * Get authentication token from localStorage
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Remove authentication token from localStorage
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Store user data in localStorage
 */
export const setUser = (user: User): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * Get user data from localStorage
 */
export const getUser = (): User | null => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

/**
 * Remove user data from localStorage
 */
export const removeUser = (): void => {
  localStorage.removeItem(USER_KEY);
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  return !!getToken();
};

/**
 * Login user
 */
export const login = async (email: string, password: string): Promise<LoginResponse> => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.error.message || 'Login failed');
  }

  const data: LoginResponse = await response.json();

  // Store token and user data
  setToken(data.token);
  setUser(data.user);

  return data;
};

/**
 * Register new user
 */
export const register = async (email: string, password: string): Promise<RegisterResponse> => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.error.message || 'Registration failed');
  }

  const data: RegisterResponse = await response.json();

  return data;
};

/**
 * Logout user
 */
export const logout = (): void => {
  removeToken();
  removeUser();
  window.location.href = '/login';
};

/**
 * Get authorization headers for API requests
 */
export const getAuthHeaders = (): HeadersInit => {
  const token = getToken();

  if (!token) {
    return {
      'Content-Type': 'application/json',
    };
  }

  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};
