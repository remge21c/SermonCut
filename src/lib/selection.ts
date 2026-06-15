// 쇼츠 후보 선택 로직 (순수 함수) — specs/screens/quick-candidates.yaml
// 정확히 3개 선택 규칙을 캡슐화.

export interface Candidate {
  id: string;
  score?: number;
  [k: string]: unknown;
}

export const SELECTED_COUNT = 3;

/** id 선택 토글. 이미 선택 → 해제. 미선택 & 한도 미만 → 추가. 한도 도달 시 추가 무시. */
export function toggleSelection(
  selected: string[],
  id: string,
  max = SELECTED_COUNT
): string[] {
  if (selected.includes(id)) {
    return selected.filter((s) => s !== id);
  }
  if (selected.length >= max) {
    return selected; // 한도 초과 → 변경 없음
  }
  return [...selected, id];
}

/** 정확히 required개 선택되었는지 */
export function canConfirm(selected: string[], required = SELECTED_COUNT): boolean {
  return selected.length === required;
}

/** AI 추천(selected_candidate_ids) 우선, 없으면 점수 상위 N개를 기본 선택 */
export function defaultSelection(
  candidates: Candidate[],
  recommended?: string[],
  count = SELECTED_COUNT
): string[] {
  const ids = new Set(candidates.map((c) => c.id));
  const valid = (recommended ?? []).filter((id) => ids.has(id));
  if (valid.length === count) return valid;

  return [...candidates]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .slice(0, count)
    .map((c) => c.id);
}
