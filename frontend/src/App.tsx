import { useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  LoaderCircle,
  RefreshCcw,
  Sparkles,
  UploadCloud,
} from "lucide-react";

type Stage = {
  stage: string;
  replicas: string[];
};

type Mistake = {
  type: string;
  description: string;
};

type Recommendation = {
  problem: string;
  reason: string;
  recommendation: string;
};

type Report = {
  summary: {
    short_summary?: string;
    result?: string;
  };
  dialog_stages: Stage[];
  script_analysis: {
    followed_score?: number;
    missing_stages?: string[];
    violations?: string[];
    comment?: string;
  };
  mistakes: Mistake[];
  recommendations: Recommendation[];
};

type UploadResponse = {
  call_id: string;
  filename: string;
  transcript: string;
  report: Report;
  report_path: string;
  status: string;
};

type Screen = "upload" | "processing" | "report";

const DEMO_RESULT: UploadResponse = {
  call_id: "demo-call-001",
  filename: "perfect_call.mp3",
  transcript: `Менеджер: Добрый день! Меня зовут Анна, компания Альфа. Вам удобно говорить?
Клиент: Да, пару минут есть.
Менеджер: Подскажите, как сейчас у вас устроен контроль качества звонков?
Клиент: Пока вручную, выборочно слушаем разговоры.
Менеджер: Поняла. Мы как раз помогаем автоматизировать такой анализ: выделяем этапы диалога, нарушения скрипта и ошибки менеджеров.
Клиент: А рекомендации тоже даёте?
Менеджер: Да, после каждого звонка формируется коучинговый отчёт с рекомендациями для следующего разговора.
Клиент: Звучит интересно.
Менеджер: Давайте я отправлю материалы и предложу пилот на небольшой группе сотрудников.
Клиент: Хорошо, отправляйте.`,
  report_path: "reports/demo-call-001_report.json",
  status: "processed",
  report: {
    summary: {
      short_summary:
        "Менеджер корректно начал разговор, выявил текущий подход клиента к контролю качества звонков, презентовал решение и довёл разговор до следующего шага — отправки материалов и предложения пилота.",
      result:
        "Звонок можно считать успешным: контакт установлен, потребность выявлена, решение представлено, следующий шаг зафиксирован.",
    },
    dialog_stages: [
      {
        stage: "Приветствие",
        replicas: [
          "Менеджер: Добрый день! Меня зовут Анна, компания Альфа. Вам удобно говорить?",
        ],
      },
      {
        stage: "Выявление потребности",
        replicas: [
          "Менеджер: Подскажите, как сейчас у вас устроен контроль качества звонков?",
          "Клиент: Пока вручную, выборочно слушаем разговоры.",
        ],
      },
      {
        stage: "Презентация решения",
        replicas: [
          "Менеджер: Мы как раз помогаем автоматизировать такой анализ: выделяем этапы диалога, нарушения скрипта и ошибки менеджеров.",
          "Менеджер: Да, после каждого звонка формируется коучинговый отчёт с рекомендациями для следующего разговора.",
        ],
      },
      {
        stage: "Фиксация следующего шага",
        replicas: [
          "Менеджер: Давайте я отправлю материалы и предложу пилот на небольшой группе сотрудников.",
        ],
      },
    ],
    script_analysis: {
      followed_score: 89,
      missing_stages: [],
      violations: ["Недостаточно глубоко раскрыта ценность пилота для клиента."],
      comment:
        "Скрипт в целом соблюдён. Есть пространство для усиления аргументации на этапе презентации.",
    },
    mistakes: [
      {
        type: "Недостаточная конкретизация выгоды",
        description:
          'Цитата: "Мы как раз помогаем автоматизировать такой анализ". Пояснение: менеджер обозначил пользу, но не перевёл её в конкретный бизнес-результат для клиента.',
      },
    ],
    recommendations: [
      {
        problem: "Недостаточно конкретно сформулирована ценность решения",
        reason:
          "Клиенту проще принять следующий шаг, когда выгода выражена через экономию времени, рост качества контроля или снижение нагрузки на руководителя.",
        recommendation:
          "На этапе презентации добавляйте 1–2 конкретных эффекта: например, сокращение времени на разбор звонков и более быстрый персональный фидбек менеджерам.",
      },
      {
        problem: "Аргументация пилота звучит общо",
        reason:
          "Следующий шаг воспринимается лучше, когда у него понятный масштаб и ожидаемый результат.",
        recommendation:
          "Предлагайте пилот через чёткую рамку: срок, группа менеджеров, формат результата и критерии успеха.",
      },
    ],
  },
};

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [screen, setScreen] = useState<Screen>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const score = useMemo(() => {
    return result?.report?.script_analysis?.followed_score ?? 0;
  }, [result]);

  const handleSelectFile = (selected: File | null) => {
    if (!selected) return;
    setFile(selected);
    setError("");
  };

  const handleStart = async () => {
    if (!file) {
      setError("Сначала выберите аудиофайл .wav или .mp3.");
      return;
    }

    setError("");
    setScreen("processing");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE}/calls/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let message = "Не удалось обработать файл.";
        try {
          const err = await response.json();
          message = err?.detail || message;
        } catch {
          // ignore
        }
        throw new Error(message);
      }

      const data: UploadResponse = await response.json();
      setResult(data);
      setScreen("report");
    } catch (err: any) {
      console.error(err);
      setError(
        `Не удалось получить ответ от backend. Сейчас показываю демо-отчёт. ${
          err?.message ? `Причина: ${err.message}` : ""
        }`
      );

      setTimeout(() => {
        setResult({
          ...DEMO_RESULT,
          filename: file.name,
        });
        setScreen("report");
      }, 800);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError("");
    setScreen("upload");
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#F4F1EA] text-[#111111]">
      <Decor />

      {screen === "upload" && (
        <main className="relative z-10 mx-auto flex min-h-screen max-w-[1440px] items-center px-6 py-12 md:px-12 lg:px-20">
          <div className="grid w-full grid-cols-1 gap-14 lg:grid-cols-[1.12fr_0.88fr] lg:items-center">
            <section className="max-w-[760px]">
              <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#728A7530] bg-white/60 px-4 py-2 text-sm text-[#5A705D] backdrop-blur-sm">
                <Sparkles size={16} />
                AI-веб-сервис для анализа звонков
              </div>

              <h1 className="max-w-[760px] text-5xl font-semibold leading-[0.98] tracking-[-0.045em] md:text-6xl lg:text-7xl">
                Анализ звонков
                <br />
                <span className="text-[#728A75]">для обучения</span>
                <br />
                менеджеров
              </h1>

              <p className="mt-8 max-w-[620px] text-lg leading-8 text-[#535353] md:text-xl">
                Загрузите запись звонка, чтобы получить структурированный
                AI-отчёт: этапы диалога, ошибки, соблюдение скрипта и
                рекомендации для следующего разговора.
              </p>

              <div className="mt-10 flex flex-wrap gap-3 text-sm text-[#2E2E2E]">
                <span className="rounded-full border border-[#DADFD6] bg-white/70 px-4 py-2">
                  Speech-to-Text
                </span>
                <span className="rounded-full border border-[#DADFD6] bg-white/70 px-4 py-2">
                  LLM-анализ
                </span>
                <span className="rounded-full border border-[#DADFD6] bg-white/70 px-4 py-2">
                  RAG
                </span>
                <span className="rounded-full border border-[#DADFD6] bg-white/70 px-4 py-2">
                  Коучинговый отчёт
                </span>
              </div>
            </section>

            <section className="relative">
              <div className="rounded-[34px] border border-white/70 bg-white/68 p-6 shadow-[0_20px_80px_rgba(0,0,0,0.06)] backdrop-blur-md md:p-8">
                <div className="mb-8 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm uppercase tracking-[0.22em] text-[#728A75]">
                      upload call
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
                      Загрузка звонка
                    </h2>
                  </div>
                  <div className="rounded-full border border-[#E5EBE1] px-3 py-1 text-sm text-[#637866]">
                    .wav / .mp3
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setIsDragging(false);
                    const dropped = e.dataTransfer.files?.[0] ?? null;
                    handleSelectFile(dropped);
                  }}
                  className={`group flex min-h-[250px] w-full flex-col items-center justify-center rounded-[30px] border bg-[#F8F5EE] px-6 text-center transition duration-300 ${
                    isDragging
                      ? "border-[#728A75] border-solid bg-[#F2EEE5]"
                      : "border-dashed border-[#AAB8A8] hover:border-[#728A75] hover:bg-[#F2EEE5]"
                  }`}
                >
                  <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-white shadow-sm">
                    <UploadCloud size={30} className="text-[#728A75]" />
                  </div>

                  <p className="text-lg font-medium text-[#222222]">
                    {file ? file.name : "Перетащите файл или нажмите для загрузки"}
                  </p>

                  <p className="mt-3 max-w-[390px] text-sm leading-6 text-[#6D6D6D]">
                    После загрузки система расшифрует аудио, проанализирует
                    структуру разговора и сформирует коучинговый отчёт.
                  </p>

                  <input
                    ref={inputRef}
                    type="file"
                    accept=".wav,.mp3,audio/*"
                    className="hidden"
                    onChange={(e) => {
                      const selected = e.target.files?.[0] ?? null;
                      handleSelectFile(selected);
                    }}
                  />
                </button>

                {error && (
                  <div className="mt-5 flex items-start gap-3 rounded-2xl border border-[#E8D7D1] bg-[#FFF6F3] px-4 py-3 text-left text-sm text-[#8A4E3B]">
                    <AlertCircle size={18} className="mt-0.5 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <button
                  onClick={handleStart}
                  className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#728A75] px-6 py-4 text-base font-medium text-white transition hover:bg-[#617764]"
                >
                  Запустить анализ
                  <ArrowRight size={18} />
                </button>

                <div className="mt-5 flex items-center justify-between text-sm text-[#727272]">
                  <span>Фокус на развитии менеджера</span>
                  <span>AI report</span>
                </div>
              </div>
            </section>
          </div>
        </main>
      )}

      {screen === "processing" && (
        <main className="relative z-10 flex min-h-screen items-center justify-center px-6">
          <div className="w-full max-w-[560px] rounded-[32px] border border-white/60 bg-white/58 p-9 text-center shadow-[0_18px_60px_rgba(0,0,0,0.045)] backdrop-blur-md">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-[#EFF3EC]">
              <LoaderCircle className="animate-spin text-[#6F8A74]" size={28} />
            </div>

            <p className="mb-3 text-sm uppercase tracking-[0.22em] text-[#6F8A74]">
              processing
            </p>

            <h2 className="text-[2rem] font-medium tracking-[-0.03em]">
              Идёт анализ звонка
            </h2>

            <p className="mx-auto mt-5 max-w-[460px] text-base leading-7 text-[#5B5B5B]">
              Мы расшифровываем аудио, анализируем структуру диалога, проверяем
              соблюдение скрипта и формируем коучинговый отчёт.
            </p>

            <div className="mt-8 rounded-full bg-[#EEF2EC] p-2">
              <div className="h-2 w-2/3 rounded-full bg-[#6F8A74]" />
            </div>

            <p className="mt-4 text-sm text-[#6D6D6D]">
              Файл:{" "}
              <span className="font-medium text-[#2A2A2A]">
                {file?.name || "—"}
              </span>
            </p>
          </div>
        </main>
      )}

      {screen === "report" && result && (
        <main className="relative z-10 mx-auto max-w-[1440px] px-6 py-10 md:px-10 lg:px-16">
          <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#728A7530] bg-white/60 px-4 py-2 text-sm text-[#5A705D] backdrop-blur-sm">
                <CheckCircle2 size={16} />
                Анализ завершён
              </div>
              <h1 className="text-4xl font-semibold tracking-[-0.04em] md:text-5xl">
                Отчёт по звонку
              </h1>
              <p className="mt-3 text-base text-[#5B5B5B]">
                Файл: <span className="font-medium">{result.filename}</span>
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleReset}
                className="inline-flex items-center gap-2 rounded-full border border-[#D8DED5] bg-white/70 px-5 py-3 text-sm font-medium text-[#364236] transition hover:bg-white"
              >
                <ArrowLeft size={16} />
                Загрузить другой файл
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-2xl border border-[#E8D7D1] bg-[#FFF6F3] px-4 py-3 text-left text-sm text-[#8A4E3B]">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <GlassCard>
              <CardLabel>summary</CardLabel>
              <CardTitle>Краткое резюме</CardTitle>
              <p className="mt-4 text-[15px] leading-7 text-[#505050]">
                {result.report.summary?.short_summary || "Нет данных."}
              </p>
              <div className="mt-6 rounded-[24px] bg-[#F7F4ED] p-5">
                <p className="text-sm uppercase tracking-[0.18em] text-[#728A75]">
                  результат звонка
                </p>
                <p className="mt-2 text-lg leading-8 text-[#222]">
                  {result.report.summary?.result || "Нет данных."}
                </p>
              </div>
            </GlassCard>

            <GlassCard>
              <CardLabel>script</CardLabel>
              <CardTitle>Следование скрипту</CardTitle>

              <div className="mt-5 flex items-end gap-3">
                <span className="text-5xl font-semibold tracking-[-0.04em] text-[#728A75]">
                  {score}
                </span>
                <span className="pb-1 text-sm text-[#727272]">/ 100</span>
              </div>

              <div className="mt-4 h-3 rounded-full bg-[#EAEFE8]">
                <div
                  className="h-3 rounded-full bg-[#728A75] transition-all"
                  style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
                />
              </div>

              <div className="mt-6 space-y-4 text-sm text-[#555]">
                <div>
                  <p className="mb-2 font-medium text-[#222]">Пропущенные этапы</p>
                  {result.report.script_analysis?.missing_stages?.length ? (
                    <ul className="list-disc pl-5 leading-6">
                      {result.report.script_analysis.missing_stages.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>Пропущенные этапы не обнаружены.</p>
                  )}
                </div>

                <div>
                  <p className="mb-2 font-medium text-[#222]">Нарушения</p>
                  {result.report.script_analysis?.violations?.length ? (
                    <ul className="list-disc pl-5 leading-6">
                      {result.report.script_analysis.violations.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>Выраженных нарушений не обнаружено.</p>
                  )}
                </div>

                {result.report.script_analysis?.comment && (
                  <div className="rounded-2xl bg-[#F7F4ED] p-4 leading-6">
                    {result.report.script_analysis.comment}
                  </div>
                )}
              </div>
            </GlassCard>
          </section>

          <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <GlassCard>
              <CardLabel>dialog stages</CardLabel>
              <CardTitle>Этапы диалога</CardTitle>

              <div className="mt-5 space-y-4">
                {result.report.dialog_stages?.length ? (
                  result.report.dialog_stages.map((stage, index) => (
                    <div
                      key={`${stage.stage}-${index}`}
                      className="rounded-[24px] bg-[#F7F4ED] p-5"
                    >
                      <div className="mb-3 inline-flex rounded-full border border-[#D8DED5] bg-white/70 px-3 py-1 text-xs uppercase tracking-[0.18em] text-[#728A75]">
                        {stage.stage || "Этап"}
                      </div>

                      <div className="space-y-2">
                        {stage.replicas?.length ? (
                          stage.replicas.map((replica, i) => (
                            <p
                              key={i}
                              className="text-sm leading-6 text-[#4E4E4E]"
                            >
                              {replica}
                            </p>
                          ))
                        ) : (
                          <p className="text-sm text-[#6A6A6A]">Нет реплик.</p>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[#6A6A6A]">
                    Этапы диалога отсутствуют.
                  </p>
                )}
              </div>
            </GlassCard>

            <GlassCard>
              <CardLabel>mistakes</CardLabel>
              <CardTitle>Ошибки менеджера</CardTitle>

              <div className="mt-5 space-y-4">
                {result.report.mistakes?.length ? (
                  result.report.mistakes.map((mistake, index) => (
                    <div
                      key={`${mistake.type}-${index}`}
                      className="rounded-[24px] border border-[#F0DDD4] bg-[#FFF8F5] p-5"
                    >
                      <p className="text-sm uppercase tracking-[0.18em] text-[#9A5E47]">
                        {mistake.type || "Ошибка"}
                      </p>
                      <p className="mt-3 text-sm leading-6 text-[#555]">
                        {mistake.description || "Описание не указано."}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-[24px] bg-[#F4F8F1] p-5 text-sm text-[#4F6B50]">
                    Явные ошибки не обнаружены.
                  </div>
                )}
              </div>
            </GlassCard>
          </section>

          <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[0.95fr_1.05fr]">
            <GlassCard>
              <CardLabel>recommendations</CardLabel>
              <CardTitle>Рекомендации</CardTitle>

              <div className="mt-5 space-y-4">
                {result.report.recommendations?.length ? (
                  result.report.recommendations.map((item, index) => (
                    <div
                      key={index}
                      className="rounded-[24px] bg-[#F7F4ED] p-5"
                    >
                      <p className="text-sm uppercase tracking-[0.18em] text-[#728A75]">
                        Зона роста
                      </p>
                      <p className="mt-2 text-base font-medium text-[#232323]">
                        {item.problem || "Не указано"}
                      </p>

                      <p className="mt-4 text-sm uppercase tracking-[0.18em] text-[#8A8A8A]">
                        Почему это важно
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#565656]">
                        {item.reason || "Не указано"}
                      </p>

                      <p className="mt-4 text-sm uppercase tracking-[0.18em] text-[#8A8A8A]">
                        Что улучшать
                      </p>
                      <p className="mt-2 text-sm leading-6 text-[#565656]">
                        {item.recommendation || "Не указано"}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[#6A6A6A]">
                    Рекомендации отсутствуют.
                  </p>
                )}
              </div>
            </GlassCard>

            <GlassCard>
              <CardLabel>transcript</CardLabel>
              <CardTitle>Транскрипт</CardTitle>

              <div className="mt-5 rounded-[24px] bg-[#F7F4ED] p-5">
                <p className="whitespace-pre-line text-sm leading-7 text-[#4F4F4F]">
                  {result.transcript || "Транскрипт отсутствует."}
                </p>
              </div>

              <button
                onClick={() => {
                  setScreen("processing");
                  setTimeout(() => setScreen("report"), 700);
                }}
                className="mt-5 inline-flex items-center gap-2 rounded-full border border-[#D8DED5] bg-white/70 px-4 py-3 text-sm font-medium text-[#364236] transition hover:bg-white"
              >
                <RefreshCcw size={15} />
                Обновить экран
              </button>
            </GlassCard>
          </section>
        </main>
      )}
    </div>
  );
}

function Decor() {
  return (
    <>
      <svg
        className="pointer-events-none absolute left-0 top-0 w-full opacity-40"
        viewBox="0 0 1440 220"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M-80 80C92 22 239 18 391 57C552 98 669 158 834 154C999 150 1096 82 1241 49C1334 28 1414 30 1520 57"
          stroke="#728A75"
          strokeWidth="1"
        />
        <path
          d="M-90 120C69 73 231 61 396 94C559 127 674 183 834 181C1004 179 1114 118 1254 88C1350 67 1437 69 1530 95"
          stroke="#9AAD9B"
          strokeWidth="0.8"
        />
      </svg>

      <svg
        className="pointer-events-none absolute bottom-0 right-0 w-full opacity-35"
        viewBox="0 0 1440 240"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M-20 171C122 132 239 116 364 135C492 154 598 208 724 211C867 214 971 158 1096 129C1228 98 1333 100 1475 143"
          stroke="#728A75"
          strokeWidth="0.95"
        />
        <path
          d="M-31 208C105 169 226 154 357 172C487 190 604 235 729 238C866 241 971 194 1091 166C1224 135 1339 139 1470 178"
          stroke="#AAB8A8"
          strokeWidth="0.75"
        />
      </svg>

      <div className="pointer-events-none absolute right-[7%] top-[10%] opacity-35">
        <svg
          width="180"
          height="180"
          viewBox="0 0 180 180"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M90 90
               m 0 -4
               a 4 4 0 1 1 -8 0
               a 8 8 0 1 0 16 0
               a 16 16 0 1 1 -32 0
               a 24 24 0 1 0 48 0
               a 32 32 0 1 1 -64 0
               a 40 40 0 1 0 80 0
               a 48 48 0 1 1 -96 0"
            stroke="#7E907F"
            strokeWidth="1"
            strokeLinecap="round"
          />
        </svg>
      </div>
    </>
  );
}

function GlassCard({ children }: { children: React.ReactNode }) {
  return (
    <section className="rounded-[32px] border border-white/70 bg-white/62 p-6 shadow-[0_18px_60px_rgba(0,0,0,0.045)] backdrop-blur-md md:p-7">
      {children}
    </section>
  );
}

function CardLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-sm uppercase tracking-[0.22em] text-[#728A75]">
      {children}
    </p>
  );
}

function CardTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em]">
      {children}
    </h2>
  );
}