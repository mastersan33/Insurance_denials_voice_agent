import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { ArrowLeft, Mail, Loader2, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

const schema = z.object({
  email: z.string().email('Enter a valid email'),
});
type FormValues = z.infer<typeof schema>;

export default function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    await api.post('/api/v1/auth/forgot-password', { email: values.email });
    setSubmittedEmail(values.email);
    setSent(true);
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12 bg-background">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-sm"
      >
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-8 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to sign in
        </Link>

        {sent ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center"
          >
            <div className="flex justify-center mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-success/10">
                <CheckCircle className="h-6 w-6 text-success" />
              </div>
            </div>
            <h2 className="text-xl font-bold text-foreground mb-2">Check your email</h2>
            <p className="text-sm text-muted-foreground">
              We sent a reset link to{' '}
              <span className="font-medium text-foreground">{submittedEmail}</span>.
              The link expires in 60 minutes.
            </p>
            <p className="text-xs text-muted-foreground mt-4">
              Didn't receive it?{' '}
              <button
                onClick={() => setSent(false)}
                className="text-primary hover:underline"
              >
                Try again
              </button>
            </p>
          </motion.div>
        ) : (
          <>
            <div className="flex items-center justify-center h-12 w-12 rounded-full bg-primary/10 mb-6">
              <Mail className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-1">Forgot password?</h1>
            <p className="text-sm text-muted-foreground mb-8">
              Enter your email and we'll send a reset link.
            </p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">Email</label>
                <input
                  {...register('email')}
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.com"
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                />
                {errors.email && (
                  <p className="text-xs text-destructive">{errors.email.message}</p>
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
                    Sending…
                  </>
                ) : (
                  'Send reset link'
                )}
              </button>
            </form>
          </>
        )}
      </motion.div>
    </div>
  );
}
