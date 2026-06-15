import { useEffect, useRef, useState } from "react";
import { formatTimecode } from "../lib/time";

interface Props {
  path: string;          // 절대 또는 프로젝트 상대 경로
  start?: number;        // 구간 시작(초)
  end?: number;          // 구간 끝(초)
  autoPlay?: boolean;
}

/**
 * 로컬 영상/결과 파일을 media:// 로 재생.
 * start/end 가 있으면 JS로 해당 구간만 재생(메타데이터 로드 시 start로 이동, end에서 정지).
 */
export function MediaVideo({ path, start, end, autoPlay = true }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const ref = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    let alive = true;
    window.sermoncut.mediaUrl(path).then((u) => alive && setUrl(u));
    return () => {
      alive = false;
    };
  }, [path]);

  const hasSegment = start != null && end != null;

  function seekToStart() {
    const v = ref.current;
    if (v && start != null) v.currentTime = start;
  }

  function onTimeUpdate() {
    const v = ref.current;
    if (v && end != null && v.currentTime >= end) {
      v.pause();
    }
  }

  if (!url) return <div className="video-loading">영상 불러오는 중…</div>;

  return (
    <div className="media-video">
      {hasSegment && (
        <div className="seg-bar">
          <span className="seg-time">
            {formatTimecode(start!)} ~ {formatTimecode(end!)} ({Math.round(end! - start!)}초)
          </span>
          <button className="btn-ghost btn-ghost--sm" onClick={() => { seekToStart(); ref.current?.play(); }}>
            ↺ 구간 처음부터
          </button>
        </div>
      )}
      <video
        ref={ref}
        className="preview-video"
        src={url}
        controls
        autoPlay={autoPlay}
        onLoadedMetadata={seekToStart}
        onTimeUpdate={onTimeUpdate}
      />
    </div>
  );
}
