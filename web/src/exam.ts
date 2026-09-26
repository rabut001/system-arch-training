export const CHOICES = ["ア", "イ", "ウ", "エ"] as const;

export const EXAM_IDS = [
  "2025-r07-haru",
  "2024-r06-haru",
  "2023-r05-haru",
  "2022-r04-haru",
  "2021-r03-haru",
  "2019-r01-aki",
  "2018-h30-aki",
  "2017-h29-aki",
  "2016-h28-aki",
  "2015-h27-aki",
  "2014-h26-aki",
  "2013-h25-aki",
  "2012-h24-aki",
  "2011-h23-aki",
  "2010-h22-aki",
  "2009-h21-aki",
] as const;

export type ExamId = (typeof EXAM_IDS)[number];

export function isExamId(value: string): value is ExamId {
  return (EXAM_IDS as readonly string[]).includes(value);
}

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

const examCache = new Map<string, Promise<Exam>>();
const resolvedExams = new Map<string, Exam>();

export function peekExam(examId: string): Exam | undefined {
  return resolvedExams.get(examId);
}

export function loadExam(examId: string): Promise<Exam> {
  const cached = examCache.get(examId);
  if (cached) {
    return cached;
  }
  const pending = fetchExam(examId)
    .then((exam) => {
      resolvedExams.set(examId, exam);
      return exam;
    })
    .catch((error: unknown) => {
      examCache.delete(examId);
      throw error;
    });
  examCache.set(examId, pending);
  return pending;
}

async function fetchExam(examId: string): Promise<Exam> {
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
