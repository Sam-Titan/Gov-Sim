import { getHealth } from "@/api";
import { getHealthQueryKey } from "@/api/@tanstack/react-query.gen";

export const HEALTH_POLL_MS = 3000;
export const HEALTH_TIMEOUT_MS = 10000;

// Render's free plan answers 502/503/504 (or hangs) while the backend starts. Every failure
// here means "still waking": the query throws, App keeps polling and shows the wake-up
// screen, never an error screen.
export function healthQuery(timeoutMs = HEALTH_TIMEOUT_MS) {
  return {
    queryKey: getHealthQueryKey(),
    queryFn: async ({ signal }: { signal: AbortSignal }) => {
      const { data } = await getHealth({
        signal: AbortSignal.any([signal, AbortSignal.timeout(timeoutMs)]),
        throwOnError: true,
      });
      return data;
    },
    refetchInterval: (q: { state: { data?: unknown } }) => (q.state.data ? false : HEALTH_POLL_MS),
    retry: false,
  } as const;
}
