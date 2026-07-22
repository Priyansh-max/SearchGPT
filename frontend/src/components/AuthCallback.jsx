import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { me, setToken } from '../services/auth';

/**
 * Landing route for the backend Google OAuth redirect.
 * Backend redirects to: {FRONTEND_URL}/auth/callback?token=<jwt>&next=<path>
 */
const AuthCallback = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const token = params.get('token');
    const next = params.get('next') || '/';
    const finish = async () => {
      if (!token) {
        navigate('/signin', { replace: true });
        return;
      }
      setToken(token);
      const current = await me();
      const destination = current?.onboarding_completed ? next : `/onboarding?next=${encodeURIComponent(next)}`;
      navigate(destination, { replace: true });
    };
    finish();
  }, [params, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-black">
      <p className="text-sm text-gray-500 dark:text-neutral-400">Signing you in…</p>
    </div>
  );
};

export default AuthCallback;
