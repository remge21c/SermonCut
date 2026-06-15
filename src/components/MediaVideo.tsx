import { useEffect, useState } from "react";

interface Props {
  path: string;          // 절대 또는 프로젝트 상대 경로
  start?: number;        // 구간 시작(초) — 미디어 프래그먼트
  end?: number;          // 구간 끝(초)
  autoPlay?: boolean;
}

/** 로컬 영상/결과 파일을 media:// 로 해석해 재생. start/end 지정 시 해당 구간만. */
export function MediaVideo({ path, start, end, autoPlay = true }: Props) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    window.sermoncut.mediaUrl(path).then((u) => alive && setUrl(u));
    return () => {
      alive = false;
    };
  }, [path]);

  if (!url) return <div className="video-loading">영상 불러오는 중…</div>;

  const frag =
    start != null && end != null
      ? `#t=${start},${end}`
      : start != null
        ? `#t=${start}`
        : "";

  return (
    <video className="preview-video" src={url + frag} controls autoPlay={autoPlay} />
  );
}
