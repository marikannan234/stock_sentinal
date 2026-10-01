'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { alertService } from '@/lib/api-service';
import { queryKeys } from '@/lib/query-keys';
import type { AlertItem } from '@/lib/types';
import { useIsAuthenticated } from './use-is-authenticated';

/**
 * The backend checks alerts every 30 s, and a fired alert turns inactive on the
 * server. Within that window the shell bell and the Alerts page reuse the
 * cached list instead of refetching on every navigation; user edits refresh it
 * immediately through the mutations below.
 */
const ALERTS_STALE_TIME_MS = 30_000;

export type CreateAlertPayload = Parameters<typeof alertService.create>[0];

/** The signed-in user's alerts, shared by the Alerts page and the shell bell. */
export function useAlertsQuery() {
  const isAuthenticated = useIsAuthenticated();
  return useQuery({
    queryKey: queryKeys.alerts.all,
    queryFn: () => alertService.list(),
    enabled: isAuthenticated,
    staleTime: ALERTS_STALE_TIME_MS,
  });
}

function useInvalidateAlerts() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: queryKeys.alerts.all });
}

export function useCreateAlertMutation() {
  const invalidateAlerts = useInvalidateAlerts();
  return useMutation({
    mutationFn: (payload: CreateAlertPayload) => alertService.create(payload),
    onSuccess: invalidateAlerts,
  });
}

/** Pause or resume an alert; resuming a fired alert re-arms it on the server. */
export function useSetAlertActiveMutation() {
  const queryClient = useQueryClient();
  const invalidateAlerts = useInvalidateAlerts();
  return useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => alertService.update(id, isActive),
    onSuccess: (updated) => {
      // Show the server's version of the alert at once, then refetch the list.
      queryClient.setQueryData<AlertItem[]>(queryKeys.alerts.all, (alerts) =>
        alerts?.map((alert) => (alert.id === updated.id ? updated : alert)),
      );
      return invalidateAlerts();
    },
  });
}

export function useDeleteAlertMutation() {
  const queryClient = useQueryClient();
  const invalidateAlerts = useInvalidateAlerts();
  return useMutation({
    mutationFn: (id: number) => alertService.remove(id),
    onSuccess: (_, id) => {
      queryClient.setQueryData<AlertItem[]>(queryKeys.alerts.all, (alerts) =>
        alerts?.filter((alert) => alert.id !== id),
      );
      return invalidateAlerts();
    },
  });
}
