export const CHOICES = ["ア", "イ", "ウ", "エ"] as const;

export type Choice = (typeof CHOICES)[number];

export type Question = {
  no: number;
  answer: Choice;
  image: string;
  explanation: string;
};

export type Exam = {
  id: string;
  title: string;
  questions: Question[];
};

function isChoice(value: unknown): value is Choice {
  return typeof value === "string" && CHOICES.includes(value as Choice);
}

function isQuestion(value: unknown): value is Question {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const question = value as Record<string, unknown>;
  return (
    typeof question.no === "number" &&
    isChoice(question.answer) &&
    typeof question.image === "string" &&
    typeof question.explanation === "string"
  );
}

export function parseExam(value: unknown): Exam {
  if (typeof value !== "object" || value === null) {
    throw new Error("問題データの形式が不正です。");
  }
  const exam = value as Record<string, unknown>;
  if (
    typeof exam.id !== "string" ||
    typeof exam.title !== "string" ||
    !Array.isArray(exam.questions) ||
    !exam.questions.every(isQuestion)
  ) {
    throw new Error("問題データの形式が不正です。");
  }
  return {
    id: exam.id,
    title: exam.title,
    questions: exam.questions,
  };
}

export async function loadExam(examId: string): Promise<Exam> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/${examId}.json`);
  if (!response.ok) {
    throw new Error("問題データを読み込めませんでした。");
  }
  const exam = parseExam(await response.json());
  if (exam.id !== examId) {
    throw new Error("問題データの id が一致しません。");
  }
  return exam;
}

export function imageUrl(image: string): string {
  return `${import.meta.env.BASE_URL}data/${image}`;
}
