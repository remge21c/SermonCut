import { describe, it, expect } from "vitest";
import { formatDuration, formatTimecode } from "./time";

describe("formatDuration", () => {
  it("60초 미만은 초만", () => {
    expect(formatDuration(0)).toBe("0초");
    expect(formatDuration(12_000)).toBe("12초");
    expect(formatDuration(59_900)).toBe("59초");
  });
  it("60초 이상은 분+초", () => {
    expect(formatDuration(60_000)).toBe("1분 0초");
    expect(formatDuration(83_000)).toBe("1분 23초");
    expect(formatDuration(605_000)).toBe("10분 5초");
  });
  it("음수는 0초", () => {
    expect(formatDuration(-100)).toBe("0초");
  });
});

describe("formatTimecode", () => {
  it("HH:MM:SS 패딩", () => {
    expect(formatTimecode(0)).toBe("00:00:00");
    expect(formatTimecode(5)).toBe("00:00:05");
    expect(formatTimecode(1536)).toBe("00:25:36");
    expect(formatTimecode(4507)).toBe("01:15:07");
  });
  it("음수는 00:00:00", () => {
    expect(formatTimecode(-5)).toBe("00:00:00");
  });
});
