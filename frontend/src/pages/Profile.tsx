import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { User, Lock, Loader2, CheckCircle, Camera } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { api } from '../services/api';

const profileSchema = z.object({
  full_name: z.string().min(2, 'Name must be at least 2 characters'),
  avatar_url: z.string().url('Enter a valid URL').optional().or(z.literal('')),
});
type ProfileValues = z.infer<typeof profileSchema>;

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Required'),
  new_password: z.string().min(8, 'Min. 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
});
type PasswordValues = z.infer<typeof passwordSchema>;

const ROLE_LABEL: Record<string, string> = {
  admin: 'Admin',
  supervisor: 'Supervisor',
  operator: 'Operator',
  viewer: 'Viewer',
};

export default function Profile() {
  const { user, updateUser } = useAuthStore();
  const [profileSaved, setProfileSaved] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [profileError, setProfileError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: user?.full_name ?? '', avatar_url: user?.avatar_url ?? '' },
  });

  const passwordForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', new_password: '', confirm_password: '' },
  });

  const onSaveProfile = async (values: ProfileValues) => {
    setProfileError('');
    setProfileSaved(false);
    try {
      const { data } = await api.patch('/api/v1/auth/me', {
        full_name: values.full_name,
        avatar_url: values.avatar_url || null,
      });
      updateUser(data);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setProfileError(detail || 'Failed to save profile');
    }
  };

  const onChangePassword = async (values: PasswordValues) => {
    setPasswordError('');
    setPasswordSaved(false);
    try {
      await api.post('/api/v1/auth/me/change-password', {
        current_password: values.current_password,
        new_password: values.new_password,
      });
      setPasswordSaved(true);
      passwordForm.reset();
      setTimeout(() => setPasswordSaved(false), 3000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setPasswordError(detail || 'Failed to change password');
    }
  };

  const initials = user?.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) ?? '??';

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-foreground">Profile</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage your personal information and security settings
        </p>
      </div>

      {/* Profile section */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-xl border border-border bg-card p-6 shadow-card"
      >
        <div className="flex items-center gap-3 mb-6">
          <User className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">Personal information</h2>
        </div>

        {/* Avatar */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative">
            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt={user.full_name}
                className="h-16 w-16 rounded-full object-cover border-2 border-border"
              />
            ) : (
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center border-2 border-border">
                <span className="text-lg font-semibold text-primary">{initials}</span>
              </div>
            )}
            <div className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-background border border-border flex items-center justify-center">
              <Camera className="h-3 w-3 text-muted-foreground" />
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
            <span className="inline-flex mt-1 items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {ROLE_LABEL[user?.role ?? ''] ?? user?.role}
            </span>
          </div>
        </div>

        <form onSubmit={profileForm.handleSubmit(onSaveProfile)} className="space-y-4">
          {profileError && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
              {profileError}
            </div>
          )}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">Full name</label>
            <input
              {...profileForm.register('full_name')}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
            />
            {profileForm.formState.errors.full_name && (
              <p className="text-xs text-destructive">
                {profileForm.formState.errors.full_name.message}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">Email</label>
            <input
              value={user?.email ?? ''}
              disabled
              className="w-full rounded-lg border border-input bg-muted/50 px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">Avatar URL</label>
            <input
              {...profileForm.register('avatar_url')}
              type="url"
              placeholder="https://..."
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            {profileSaved && (
              <span className="flex items-center gap-1.5 text-sm text-success">
                <CheckCircle className="h-4 w-4" /> Saved
              </span>
            )}
            <button
              type="submit"
              disabled={profileForm.formState.isSubmitting}
              className="ml-auto flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
            >
              {profileForm.formState.isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Save changes
            </button>
          </div>
        </form>
      </motion.div>

      {/* Password section */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="rounded-xl border border-border bg-card p-6 shadow-card"
      >
        <div className="flex items-center gap-3 mb-6">
          <Lock className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">Change password</h2>
        </div>

        <form onSubmit={passwordForm.handleSubmit(onChangePassword)} className="space-y-4">
          {passwordError && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
              {passwordError}
            </div>
          )}

          {(['current_password', 'new_password', 'confirm_password'] as const).map((field) => (
            <div key={field} className="space-y-1.5">
              <label className="text-sm font-medium text-foreground capitalize">
                {field.replace(/_/g, ' ')}
              </label>
              <input
                {...passwordForm.register(field)}
                type="password"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
              />
              {passwordForm.formState.errors[field] && (
                <p className="text-xs text-destructive">
                  {passwordForm.formState.errors[field]?.message}
                </p>
              )}
            </div>
          ))}

          <div className="flex items-center justify-between pt-2">
            {passwordSaved && (
              <span className="flex items-center gap-1.5 text-sm text-success">
                <CheckCircle className="h-4 w-4" /> Password updated
              </span>
            )}
            <button
              type="submit"
              disabled={passwordForm.formState.isSubmitting}
              className="ml-auto flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
            >
              {passwordForm.formState.isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Update password
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
