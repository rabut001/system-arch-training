import { useEffect, useState } from "react";
import { loadExam, type Exam } from "./exam.ts";
import { Practice } from "./Practice.tsx";

const examId = "2025-r07-haru";

export function App() {
  const [exam, setExam] = useState<Exam | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    loadExam(examId)
      .then((loaded) => {
        if (active) {
          setExam(loaded);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "読み込みに失敗しました。");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return <p className="status">{error}</p>;
  }
  if (!exam) {
    return <p className="status">問題を読み込んでいます。</p>;
  }
  return <Practice exam={exam} />;
}
