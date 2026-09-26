import { useEffect, useRef, useState } from "react";
import {
  CHOICES,
  imageUrl,
  type Choice,
  type Exam,
  type Question,
} from "./exam.ts";
import {
  clearProgress,
  emptyProgress,
  loadProgress,
  saveProgress,
  type AnswerRecord,
  type Progress,
} from "./progress.ts";
import type { LinkClick } from "./route.ts";

type PracticeProps = {
  exam: Exam;
  listHref: string;
  onLinkClick: LinkClick;
};

function questionByNo(exam: Exam, no: number): Question {
  const question = exam.questions.find((item) => item.no === no);
  if (!question) {
    return exam.questions[0];
  }
  return question;
}

function statusLabel(answer: AnswerRecord | undefined, question: Question): string {
  if (!answer) {
    return "未選択";
  }
  if (!answer.confirmed) {
    return "選択済み、未確認";
  }
  return answer.choice === question.answer ? "正解" : "誤答";
}

export function Practice({ exam, listHref, onLinkClick }: PracticeProps) {
  const [progress, setProgress] = useState<Progress>(() => loadProgress(exam.id));
  const [confirmingClear, setConfirmingClear] = useState(false);
  const imagePane = useRef<HTMLDivElement>(null);
  const dialog = useRef<HTMLDialogElement>(null);

  const questionNos = new Set(exam.questions.map((question) => question.no));
  const currentNo = questionNos.has(progress.currentNo)
    ? progress.currentNo
    : exam.questions[0].no;
  const question = questionByNo(exam, currentNo);
  const answer = progress.answers[question.no];
  const confirmed = answer?.confirmed ?? false;

  useEffect(() => {
    saveProgress(exam.id, progress);
  }, [exam.id, progress]);

  useEffect(() => {
    imagePane.current?.scrollTo(0, 0);
  }, [question.no]);

  useEffect(() => {
    const element = dialog.current;
    if (!element) {
      return;
    }
    if (confirmingClear && !element.open) {
      element.showModal();
    }
    if (!confirmingClear && element.open) {
      element.close();
    }
  }, [confirmingClear]);

  const confirmedQuestions = exam.questions.filter(
    (item) => progress.answers[item.no]?.confirmed,
  );
  const correctCount = confirmedQuestions.filter(
    (item) => progress.answers[item.no].choice === item.answer,
  ).length;
  const score =
    confirmedQuestions.length === 0
      ? "—"
      : `${correctCount}/${confirmedQuestions.length}（${Math.round(
          (correctCount / confirmedQuestions.length) * 100,
        )}%）`;

  function select(choice: Choice) {
    if (confirmed) {
      return;
    }
    setProgress((current) => ({
      ...current,
      currentNo: question.no,
      answers: {
        ...current.answers,
        [question.no]: { choice, confirmed: false },
      },
    }));
  }

  function confirmAnswer() {
    if (!answer || answer.confirmed) {
      return;
    }
    setProgress((current) => ({
      ...current,
      answers: {
        ...current.answers,
        [question.no]: { choice: answer.choice, confirmed: true },
      },
    }));
  }

  function moveTo(no: number) {
    if (!questionNos.has(no)) {
      return;
    }
    setProgress((current) => ({ ...current, currentNo: no }));
  }

  function clearSession() {
    clearProgress(exam.id);
    setProgress(emptyProgress());
    setConfirmingClear(false);
  }

  const firstNo = exam.questions[0].no;
  const lastNo = exam.questions[exam.questions.length - 1].no;

  return (
    <div className="practice">
      <header className="top">
        <a
          className="back"
          href={listHref}
          onClick={(event) => onLinkClick(event, listHref)}
        >
          一覧へ戻る
        </a>
        <div className="heading">
          <h1>{exam.title}</h1>
          <p className="score">
            正解 <span>{score}</span>
          </p>
        </div>
        <nav className="numbers" aria-label="問題番号">
          {exam.questions.map((item) => {
            const itemAnswer = progress.answers[item.no];
            const classes = ["number"];
            if (item.no === question.no) {
              classes.push("current");
            }
            if (itemAnswer?.confirmed) {
              classes.push(
                itemAnswer.choice === item.answer ? "correct" : "incorrect",
              );
            } else if (itemAnswer) {
              classes.push("draft");
            }
            return (
              <button
                key={item.no}
                type="button"
                className={classes.join(" ")}
                aria-current={item.no === question.no ? "true" : undefined}
                aria-label={`問${item.no}、${statusLabel(itemAnswer, item)}`}
                onClick={() => moveTo(item.no)}
              >
                <span>{item.no}</span>
                {itemAnswer?.confirmed && (
                  <span className="mark" aria-hidden="true">
                    {itemAnswer.choice === item.answer ? "○" : "×"}
                  </span>
                )}
                {itemAnswer && !itemAnswer.confirmed && (
                  <span className="mark" aria-hidden="true">
                    ●
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </header>

      <div className="image-pane" ref={imagePane}>
        <img src={imageUrl(question.image)} alt={`問${question.no}`} />
      </div>

      <div className="lower">
        <div className="choices" role="group" aria-label="選択肢">
          {CHOICES.map((choice) => (
            <button
              key={choice}
              type="button"
              className={answer?.choice === choice ? "selected" : undefined}
              aria-pressed={answer?.choice === choice}
              disabled={confirmed}
              onClick={() => select(choice)}
            >
              {choice}
            </button>
          ))}
        </div>

        {confirmed && answer ? (
          <section className="result" aria-live="polite">
            <p className={answer.choice === question.answer ? "ok" : "ng"}>
              {answer.choice === question.answer ? "正解" : "不正解"}
            </p>
            <p>
              正答 <strong>{question.answer}</strong>
            </p>
            <p>{question.explanation}</p>
            <p className="note">IPA の公式解説ではない</p>
          </section>
        ) : (
          <button
            type="button"
            className="confirm"
            disabled={!answer}
            onClick={confirmAnswer}
          >
            結果を確認
          </button>
        )}

        <div className="pager">
          <button
            type="button"
            disabled={question.no === firstNo}
            onClick={() => moveTo(question.no - 1)}
          >
            前へ
          </button>
          <button
            type="button"
            disabled={question.no === lastNo}
            onClick={() => moveTo(question.no + 1)}
          >
            次へ
          </button>
        </div>

        <button
          type="button"
          className="clear"
          onClick={() => setConfirmingClear(true)}
        >
          回答をすべてクリア
        </button>

        <footer>
          出典:{" "}
          <a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html">
            IPA の過去問題
          </a>
        </footer>
      </div>

      <dialog
        ref={dialog}
        onClose={() => setConfirmingClear(false)}
        aria-labelledby="clear-title"
      >
        <h2 id="clear-title">この回の解答を消します</h2>
        <p>
          {exam.title}の確認済みの解答と、まだ確認していない選択を消して、問1に戻ります。
        </p>
        <div className="dialog-actions">
          <button type="button" onClick={() => setConfirmingClear(false)}>
            中止
          </button>
          <button type="button" className="danger" onClick={clearSession}>
            消してやり直す
          </button>
        </div>
      </dialog>
    </div>
  );
}
