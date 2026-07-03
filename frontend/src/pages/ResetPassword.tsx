import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Eye, EyeOff, ArrowLeft, Loader2, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const schema = z.object({
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});
type FormValues = z.infer<typeof schema>;

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [showPassword, setShowPassword] = useState(false);
  const [done, setDone] = useState(false);
  const [serverError, setServerError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    setServerError('');
    try {
      await api.post('/api/v1/auth/reset-password', {
        token,
        new_password: values.new_password,
      });
      setDone(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setServerError(detail || 'Reset failed. The link may have expired.');
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-6">
        <div className="text-center">
          <p className="text-muted-foreground text-sm mb-4">Invalid or missing reset token.</p>
          <Link to="/forgot-password" className="text-primary hover:underline text-sm">
            Request a new link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-background">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-sm"
      >
        {done ? (
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-success/10">
                <CheckCircle className="h-6 w-6 text-success" />
              </div>
            </div>
            <h2 className="text-xl font-bold text-foreground mb-2">Password updated</h2>
            <p className="text-sm text-muted-foreground">Redirecting to sign in…</p>
          </div>
        ) : (
          <>
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to sign in
            </Link>

            <h1 className="text-2xl font-bold text-foreground mb-1">Set new password</h1>
            <p className="text-sm text-muted-foreground mb-8">
              Must be at least 8 characters.
            </p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {serverError && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
                  {serverError}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">New password</label>
                <div className="relative">
                  <input
                    {...register('new_password')}
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Min. 8 characters"
                    className="w-full rounded-lg border border-input bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {errors.new_password && (
                  <p className="text-xs text-destructive">{errors.new_password.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Confirm password</label>
                <input
                  {...register('confirm_password')}
                  type="password"
                  placeholder="Repeat password"
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                />
                {errors.confirm_password && (
                  <p className="text-xs text-destructive">{errors.confirm_password.message}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Updating…
                  </>
                ) : (
                  'Update password'
                )}
              </button>
            </form>
          </>
        )}
      </motion.div>
    </div>
  );
}
