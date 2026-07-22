import { useCallback, useState } from 'react';

const makeId = () => window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`;

export const useToasts = () => {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((message, type = 'info') => {
    const id = makeId();
    setToasts((current) => [...current, { id, message, type }].slice(-3));
    window.setTimeout(() => removeToast(id), 3200);
  }, [removeToast]);

  return { toasts, showToast, removeToast };
};
