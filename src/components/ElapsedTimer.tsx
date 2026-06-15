import { useEffect, useState } from "react";
import { formatDuration } from "../lib/time";

interface Props {
  startedAt: number | null;
  running: boolean;
  finalMs?: number | null;
}

/** 진행 중이면 실시간 카운트업, 끝나면 finalMs 고정 표시 */
export function ElapsedTimer({ startedAt, running, finalMs }: Props) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(id);
  }, [running]);

  const ms = running && startedAt ? now - startedAt : finalMs ?? 0;
  return <span className="elapsed">⏱ {formatDuration(ms)}</span>;
}
