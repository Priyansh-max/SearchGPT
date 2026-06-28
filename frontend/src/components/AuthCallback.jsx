import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { setToken } from '../services/auth';

/**
 * Landing route for the backend Google OAuth redirect.
 * Backend redirects to: {FRONTEND_URL}/auth/callback?token=<jwt>&next=<path>
 */
const AuthCallback = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const token = params.get('token');
    const next = params.get('next') || '/developers';
    if (token) {
      setToken(token);
      navigate(next, { replace: true });
    } else {
      navigate('/signin', { replace: true });
    }
  }, [params, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black">
      <p className="text-sm text-gray-500 dark:text-neutral-400">Signing you in…</p>
    </div>
  );
};

export default AuthCallback;
