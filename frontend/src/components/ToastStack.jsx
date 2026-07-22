import React from 'react';
import { FiAlertCircle, FiCheckCircle, FiInfo, FiX } from 'react-icons/fi';

const icons = {
  success: FiCheckCircle,
  error: FiAlertCircle,
  info: FiInfo,
};

const tone = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-200',
  error: 'border-red-200 bg-red-50 text-red-800 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-200',
  info: 'border-gray-200 bg-white text-gray-800 dark:border-neutral-800 dark:bg-neutral-950 dark:text-neutral-100',
};

const ToastStack = ({ toasts, onDismiss }) => (
  <div className="fixed right-4 top-4 z-[80] flex w-[min(22rem,calc(100vw-2rem))] flex-col gap-2">
    {toasts.map((toast) => {
      const Icon = icons[toast.type] || FiInfo;
      return (
        <div
          key={toast.id}
          className={`flex items-start gap-3 rounded-lg border px-3 py-3 text-sm shadow-lg backdrop-blur-md animate-[toastIn_.22s_ease-out] ${tone[toast.type] || tone.info}`}
        >
          <Icon className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="min-w-0 flex-1 leading-5">{toast.message}</div>
          <button type="button" onClick={() => onDismiss(toast.id)} className="rounded p-0.5 opacity-70 hover:opacity-100" aria-label="Dismiss notification">
            <FiX className="h-4 w-4" />
          </button>
        </div>
      );
    })}
    <style>{`@keyframes toastIn { from { opacity: 0; transform: translateY(-8px) scale(.98); } to { opacity: 1; transform: translateY(0) scale(1); } }`}</style>
  </div>
);

export default ToastStack;
