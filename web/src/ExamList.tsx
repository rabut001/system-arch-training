import { useEffect, useState } from "react";
import { EXAM_IDS, loadExam, peekExam, type Exam } from "./exam.ts";
import { examPath, listPath, type LinkClick } from "./route.ts";

type LinkProps = {
  onLinkClick: LinkClick;
};

function cachedExams(): Exam[] | null {
  const loaded = EXAM_IDS.map((id) => peekExam(id));
  if (loaded.every((exam) => exam !== undefined)) {
    return loaded;
  }
  return null;
}

export function ExamList({ onLinkClick }: LinkProps) {
  const [exams, setExams] = useState<Exam[] | null>(cachedExams);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all(EXAM_IDS.map((id) => loadExam(id)))
      .then((loaded) => {
        if (active) {
          setExams(loaded);
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
  if (!exams) {
    return <p className="status">回を読み込んでいます。</p>;
  }

  return (
    <div className="sheet">
      <h1>システムアーキテクト 午前Ⅱ</h1>
      <nav aria-label="試験の回">
        <ul className="exam-list">
          {exams.map((exam) => {
            const href = examPath(exam.id);
            return (
              <li key={exam.id}>
                <a href={href} onClick={(event) => onLinkClick(event, href)}>
                  {exam.title}
                </a>
              </li>
            );
          })}
        </ul>
      </nav>
      <footer>
        出典:{" "}
        <a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html">
          IPA の過去問題
        </a>
      </footer>
    </div>
  );
}

export function MissingExam({ onLinkClick }: LinkProps) {
  const href = listPath();
  return (
    <div className="sheet">
      <p>この回はありません。</p>
      <a className="back" href={href} onClick={(event) => onLinkClick(event, href)}>
        一覧へ戻る
      </a>
    </div>
  );
}
