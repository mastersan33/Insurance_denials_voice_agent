import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Shield, UserX, ChevronDown } from 'lucide-react';
import { usersApi } from '../services/endpoints';
import { useAuthStore } from '../store/authStore';
import { TableRowSkeleton } from '../components/Skeleton';
import { formatDistanceToNow } from 'date-fns';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string | null;
}

const ROLE_OPTIONS = ['viewer', 'operator', 'supervisor', 'admin'];

const ROLE_BADGE: Record<string, string> = {
  admin: 'bg-destructive/10 text-destructive',
  supervisor: 'bg-warning/10 text-warning',
  operator: 'bg-primary/10 text-primary',
  viewer: 'bg-muted text-muted-foreground',
};

export default function Users() {
  const qc = useQueryClient();
  const currentUser = useAuthStore((s) => s.user);

  const { data: users = [], isLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: () => usersApi.list().then((r) => r.data as User[]),
    staleTime: 30_000,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { role: string; is_active?: boolean } }) =>
      usersApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => usersApi.deactivate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  function handleRoleChange(user: User, newRole: string) {
    if (newRole === user.role) return;
    if (!window.confirm(`Change ${user.full_name}'s role to ${newRole}?`)) return;
    updateMutation.mutate({ id: user.id, data: { role: newRole } });
  }

  function handleDeactivate(user: User) {
    if (!window.confirm(`Deactivate ${user.full_name}? They will no longer be able to log in.`)) return;
    deactivateMutation.mutate(user.id);
  }

  const isAdmin = currentUser?.role === 'admin';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Users</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{users.length} total members</p>
        </div>
      </div>

      {!isAdmin && (
        <div className="rounded-lg border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-warning">
          <Shield className="inline h-4 w-4 mr-1" />
          You have read-only access. Admin role required to modify users.
        </div>
      )}

      <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/40">
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Email</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Role</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide">Last Login</th>
              {isAdmin && <th className="px-4 py-3" />}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={isAdmin ? 6 : 5} />)
              : users.length === 0
              ? (
                <tr>
                  <td colSpan={isAdmin ? 6 : 5} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    No users found
                  </td>
                </tr>
              )
              : users.map((u) => (
                <tr key={u.id} className={`hover:bg-accent/50 transition-colors ${!u.is_active ? 'opacity-50' : ''}`}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary flex-shrink-0">
                        {u.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)}
                      </div>
                      <span className="font-medium text-foreground">
                        {u.full_name}
                        {u.id === currentUser?.id && (
                          <span className="ml-1.5 text-[10px] text-muted-foreground">(you)</span>
                        )}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                  <td className="px-4 py-3">
                    {isAdmin && u.id !== currentUser?.id ? (
                      <div className="relative inline-block">
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u, e.target.value)}
                          disabled={updateMutation.isPending}
                          className={`appearance-none rounded-full pr-6 pl-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide cursor-pointer focus:outline-none ${ROLE_BADGE[u.role] ?? 'bg-muted text-muted-foreground'}`}
                        >
                          {ROLE_OPTIONS.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                        <ChevronDown className="pointer-events-none absolute right-1 top-1/2 -translate-y-1/2 h-2.5 w-2.5" />
                      </div>
                    ) : (
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${ROLE_BADGE[u.role] ?? 'bg-muted text-muted-foreground'}`}>
                        {u.role}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${u.is_active ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'}`}>
                      {u.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {u.last_login_at
                      ? formatDistanceToNow(new Date(u.last_login_at), { addSuffix: true })
                      : 'Never'}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3 text-right">
                      {u.id !== currentUser?.id && u.is_active && (
                        <button
                          onClick={() => handleDeactivate(u)}
                          disabled={deactivateMutation.isPending}
                          className="flex items-center gap-1 text-xs text-destructive hover:underline disabled:opacity-50 ml-auto"
                        >
                          <UserX className="h-3 w-3" />
                          Deactivate
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
