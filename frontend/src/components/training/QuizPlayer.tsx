import { ArrowRight, CheckCircle2, RotateCcw, Trophy, XCircle } from "lucide-react";
import { useState } from "react";
import { DEFAULT_OPERATOR_ID } from "@/api/client";
import { useQuiz, useSaveProgress } from "@/api/hooks";
import { Button, cx, EmptyState, ProgressBar, QueryBlock, Skeleton } from "@/components/ui";

/** One question at a time with instant feedback; on finish, posts 100% progress with the score. */
export function QuizPlayer({ moduleId }: { moduleId: string }) {
  const quiz = useQuiz(moduleId);
  const save = useSaveProgress();
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [correct, setCorrect] = useState(0);
  const [done, setDone] = useState(false);

  const restart = () => {
    setIndex(0);
    setPicked(null);
    setCorrect(0);
    setDone(false);
    save.reset();
  };

  return (
    <QueryBlock query={quiz} skeleton={<Skeleton className="h-72" />}>
      {({ questions }) => {
        if (questions.length === 0) return <EmptyState title="This module has no quiz yet" />;

        if (done) {
          const score = Math.round((correct / questions.length) * 100);
          return (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <Trophy className={cx("size-14", score >= 70 ? "text-accent" : "text-muted")} aria-hidden />
              <p className="text-3xl font-bold">
                {correct} / {questions.length} correct
              </p>
              <p className="tabular font-mono text-5xl font-bold text-accent">{score}%</p>
              <p className="text-muted" role="status">
                {save.isPending ? "Saving progress…" : save.isError ? `Couldn't save: ${save.error.message}` : "Progress saved"}
              </p>
              <Button icon={RotateCcw} onClick={restart}>
                Retake quiz
              </Button>
            </div>
          );
        }

        const q = questions[index];
        const answered = picked !== null;
        const isLast = index === questions.length - 1;

        const next = () => {
          if (!isLast) {
            setIndex(index + 1);
            setPicked(null);
            return;
          }
          const score = Math.round((correct / questions.length) * 100);
          save.mutate({ operator_id: DEFAULT_OPERATOR_ID, module_id: moduleId, progress_pct: 100, score });
          setDone(true);
        };

        return (
          <div>
            <div className="mb-4 flex items-center gap-3 text-sm text-muted">
              <span>
                Question {index + 1} of {questions.length}
              </span>
              <div className="flex-1">
                <ProgressBar value={(index / questions.length) * 100} label="Quiz progress" />
              </div>
            </div>
            <p className="mb-4 text-xl font-semibold">{q.prompt}</p>
            <ul className="space-y-2">
              {q.options.map((opt, i) => {
                const isAnswer = i === q.answer_index;
                const isPicked = i === picked;
                return (
                  <li key={opt}>
                    <button
                      type="button"
                      disabled={answered}
                      onClick={() => {
                        setPicked(i);
                        if (isAnswer) setCorrect((c) => c + 1);
                      }}
                      className={cx(
                        "flex min-h-14 w-full items-center gap-3 rounded-xl border px-4 text-left text-base transition",
                        !answered && "border-line bg-raised hover:border-accent",
                        answered && isAnswer && "border-good bg-good/15",
                        answered && isPicked && !isAnswer && "border-danger bg-danger/15",
                        answered && !isAnswer && !isPicked && "border-line bg-raised opacity-60",
                      )}
                    >
                      {answered && isAnswer && <CheckCircle2 className="size-5 shrink-0 text-good" aria-label="Correct answer" />}
                      {answered && isPicked && !isAnswer && <XCircle className="size-5 shrink-0 text-danger" aria-label="Your answer" />}
                      {opt}
                    </button>
                  </li>
                );
              })}
            </ul>
            {answered && (
              <div className="mt-4 space-y-3" role="status">
                <p className={cx("font-semibold", picked === q.answer_index ? "text-good" : "text-danger")}>
                  {picked === q.answer_index ? "Correct!" : "Not quite."}
                </p>
                <p className="text-muted">{q.explanation}</p>
                <Button variant="primary" icon={ArrowRight} onClick={next}>
                  {isLast ? "Finish quiz" : "Next question"}
                </Button>
              </div>
            )}
          </div>
        );
      }}
    </QueryBlock>
  );
}
