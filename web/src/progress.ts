import { CHOICES, type Choice } from "./exam.ts";

export type AnswerRecord = {
  choice: Choice;
  confirmed: boolean;
};

export type Progress = {
  currentNo: number;
  answers: Record<number, AnswerRecord>;
};

export function storageKey(examId: string): string {
  return `sa-am2:${examId}`;
}

export function emptyProgress(): Progress {
  return { currentNo: 1, answers: {} };
}

function isAnswer(value: unknown): value is AnswerRecord {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const answer = value as Record<string, unknown>;
  return (
    typeof answer.choice === "string" &&
    CHOICES.includes(answer.choice as Choice) &&
    typeof answer.confirmed === "boolean"
  );
}

export function loadProgress(examId: string): Progress {
  const raw = localStorage.getItem(storageKey(examId));
  if (raw === null) {
    return emptyProgress();
  }
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const currentNo =
      typeof parsed.currentNo === "number" ? parsed.currentNo : 1;
    const answers: Record<number, AnswerRecord> = {};
    if (typeof parsed.answers === "object" && parsed.answers !== null) {
      for (const [no, answer] of Object.entries(parsed.answers)) {
        const questionNo = Number(no);
        if (Number.isInteger(questionNo) && isAnswer(answer)) {
          answers[questionNo] = answer;
        }
      }
    }
    return { currentNo, answers };
  } catch {
    return emptyProgress();
  }
}

export function saveProgress(examId: string, progress: Progress): void {
  localStorage.setItem(storageKey(examId), JSON.stringify(progress));
}

export function clearProgress(examId: string): void {
  localStorage.removeItem(storageKey(examId));
}
