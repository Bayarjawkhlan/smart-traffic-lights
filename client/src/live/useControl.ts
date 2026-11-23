import { useCallback, useEffect, useRef, useState } from "react";
import { live } from "../api/live";
import { sendControl } from "../api/sim";
import type { ControlCommand } from "../api/types";

export function useControl() {
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const run = useCallback(async (command: ControlCommand, key: string = command.action) => {
    setPending(key);
    setError(null);
    try {
      live.applyState(await sendControl(command));
      return true;
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
      window.clearTimeout(timer.current);
      timer.current = window.setTimeout(() => setError(null), 6000);
      return false;
    } finally {
      setPending(null);
    }
  }, []);

  return { run, pending, error };
}
