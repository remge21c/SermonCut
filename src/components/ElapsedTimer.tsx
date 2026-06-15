import { useEffect, useState } from "react";

/** ms → "1분 23초" / "12초" 형식 */
export function formatDuration(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return m > 0 ? `${m}분 ${s}초` : `${s}초`;
}

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
