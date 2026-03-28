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
  type: string;
  category: string;
  text: string;
  zone_of_growth?: string;
  why_important?: string;
  what_to_improve?: string;
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

const API_BASE = "http://127.0.0.1:8000";
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB

const DEMO_RESULT: UploadResponse = {
  call_id: "demo-call-001",
  filename: "perfect_call.mp3",
  transcript: `Менеджер: Добрый день! Меня зовут Анна, компания Альфа. Вам удобно говорить?
Клиент: Да, пару минут есть.
Менеджер: Подскажите, как сейчас у вас устроен контроль качества звонков?
Клиент: Пока вручную, выборочно слушаем разговоры.
Менеджер: Мы автоматизируем анализ звонков: выделяем этапы диалога, нарушения скрипта и ошибки менеджеров.
Клиент: А рекомендации тоже даёте?
Менеджер: Да, после каждого звонка формируется коучинговый отчёт с рекомендациями.
Клиент: Звучит интересно.
Менеджер: Тогда я отправлю материалы и предложу пилот на небольшой группе сотрудников.
Клиент: Хорошо, отправляйте.`,
  report_path: "reports/demo-call-001_report.json",
  status: "processed",
  report: {
    summary: {
      short_summary:
        "Менеджер корректно установил контакт, выявил текущий процесс контроля звонков у клиента, презентовал решение и довёл разговор до следующего шага.",
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
          "Менеджер: Мы автоматизируем анализ звонков: выделяем этапы диалога, нарушения скрипта и ошибки менеджеров.",
          "Менеджер: Да, после каждого звонка формируется коучинговый отчёт с рекомендациями.",
        ],
      },
      {
        stage: "Следующий шаг",
        replicas: [
          "Менеджер: Тогда я отправлю материалы и предложу пилот на небольшой группе сотрудников.",
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
          "Фраза менеджера звучит корректно, но не переводит продукт в конкретную пользу для бизнеса клиента: экономию времени, рост качества контроля, ускорение обучения менеджеров.",
      },
    ],
    recommendations: [
      {
        type: "value_presentation",
        category: "presentation",
        text: "На этапе презентации добавляй 1–2 измеримых эффекта: сокращение времени на контроль звонков, ускорение обратной связи, повышение качества скрипта.",
        zone_of_growth: "Презентация решения",
        why_important: "Клиенту легче принять следующий шаг, если выгода выражена через понятный результат.",
        what_to_improve: "На этапе презентации добавляй 1–2 измеримых эффекта: сокращение времени на контроль звонков, ускорение обратной связи, повышение качества скрипта.",
      },
    ],
  },
};

function normalizeUploadResponse(data: UploadResponse): UploadResponse {
  const normalizedRecommendations = (data.report?.recommendations ?? []).map(
    (item: any) => ({
      ...item,
      zone_of_growth:
        item?.zone_of_growth ??
        item?.zoneOfGrowth ??
        item?.problem ??
        item?.category ??
        item?.type ??
        "Не указано",
      why_important:
        item?.why_important ??
        item?.whyImportant ??
        item?.reason ??
        "Не указано",
      what_to_improve:
        item?.what_to_improve ??
        item?.whatToImprove ??
        item?.recommendation ??
        item?.text ??
        "Не указано",
    })
  );

  const normalizedMissingStages = (data.report?.script_analysis?.missing_stages ?? []).map(
    (item: any) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object" && "stage" in item) {
        return String(item.stage);
      }
      return String(item);
    }
  );

  return {
    ...data,
    report: {
      ...data.report,
      recommendations: normalizedRecommendations,
      script_analysis: {
        ...data.report.script_analysis,
        missing_stages: normalizedMissingStages,
      },
    },
  };
}

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

    const lowerName = selected.name.toLowerCase();
    const isValidExtension =
      lowerName.endsWith(".wav") || lowerName.endsWith(".mp3");

    if (!isValidExtension) {
      setError("Можно загружать только файлы .wav и .mp3.");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    if (selected.size > MAX_FILE_SIZE) {
      setError("Файл слишком большой. Максимальный размер — 100 МБ.");
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      return;
    }

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
      const normalized = normalizeUploadResponse(data);
      setResult(normalized);
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
      }, 700);
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
    <div className="relative min-h-screen overflow-hidden bg-[#F4F1EA] text-[#121212]">
      <GlobalDecor screen={screen} />

      {screen === "upload" && (
        <main className="relative z-10 mx-auto flex min-h-screen max-w-[1480px] items-center px-6 py-10 md:px-10 xl:px-16">
          <div className="grid w-full grid-cols-1 gap-12 xl:grid-cols-[1.08fr_0.92fr] xl:items-center">
            <section className="relative max-w-[760px] pt-10 xl:pt-0">
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[#2F85781F] bg-white/55 px-4 py-2 text-sm text-[#2F8578] backdrop-blur-sm">
                <Sparkles size={16} />
                AI-веб-сервис для анализа звонков
              </div>

              <h1 className="max-w-[760px] text-5xl font-semibold leading-[0.96] tracking-[-0.05em] md:text-6xl xl:text-7xl">
                Анализ звонков
                <br />
                <span className="text-[#2F8578]">для обучения</span>
                <br />
                менеджеров
              </h1>

              <p className="mt-8 max-w-[610px] text-lg leading-8 text-[#505050] md:text-xl">
                Загрузите запись звонка, чтобы получить AI-отчёт со структурой
                диалога, ошибками, следованием скрипту и рекомендациями для
                следующего разговора.
              </p>

              <div className="mt-10 flex flex-wrap gap-3 text-sm text-[#2B2B2B]">
                <Badge text="Speech-to-Text" />
                <Badge text="LLM-анализ" />
                <Badge text="RAG" />
                <Badge text="Коучинговый отчёт" />
              </div>

              <SpiralCompact className="left-[-20px] top-[65%] hidden xl:block" />
            </section>

            <section className="relative">
              <SpiralDouble className="right-[-40px] top-[-60px] hidden xl:block" />

              <div className="relative rounded-[40px] border border-white/65 bg-white/58 p-6 shadow-[0_18px_70px_rgba(0,0,0,0.05)] backdrop-blur-md md:p-8">
                <div className="mb-8 flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm uppercase tracking-[0.22em] text-[#2F8578]">
                      upload call
                    </p>
                    <h2 className="mt-2 text-[2rem] font-semibold tracking-[-0.04em]">
                      Загрузка звонка
                    </h2>
                  </div>

                  <div className="rounded-full border border-[#DDE8E3] bg-white/55 px-3 py-1.5 text-sm text-[#5D7F73]">
                    .wav / .mp3 · до 100 МБ
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
                  className={`group flex min-h-[270px] w-full flex-col items-center justify-center rounded-[34px] border bg-[#F7F4EE] px-8 text-center transition duration-300 ${
                    isDragging
                      ? "border-[#2F8578] border-solid bg-[#F0ECE4]"
                      : "border-dashed border-[#B8C9C2] hover:border-[#2F8578] hover:bg-[#F2EEE7]"
                  }`}
                >
                  <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-[0_10px_30px_rgba(0,0,0,0.05)]">
                    <UploadCloud size={34} className="text-[#2F8578]" />
                  </div>

                  <p className="text-xl font-medium tracking-[-0.02em] text-[#1E1E1E]">
                    {file ? file.name : "Перетащите файл или нажмите для загрузки"}
                  </p>

                  <p className="mt-4 max-w-[420px] text-sm leading-7 text-[#6B6B6B]">
                    После загрузки система расшифрует аудио, проанализирует
                    структуру разговора и сформирует коучинговый отчёт.
                    Поддерживаются файлы .wav и .mp3 размером до 100 МБ.
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
                  <div className="mt-5 flex items-start gap-3 rounded-[24px] border border-[#E8D7D1] bg-[#FFF6F3] px-4 py-4 text-left text-sm leading-6 text-[#8A4E3B]">
                    <AlertCircle size={18} className="mt-0.5 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <button
                  onClick={handleStart}
                  className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#2F8578] px-6 py-4 text-base font-medium text-white transition hover:bg-[#286F65]"
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
          <SpiralSingle className="right-[7%] top-[10%] hidden xl:block" />
          <WaveLineTop />

          <div className="w-full max-w-[560px] rounded-[36px] border border-white/60 bg-white/55 p-9 text-center shadow-[0_18px_60px_rgba(0,0,0,0.04)] backdrop-blur-md">
            <div className="mx-auto mb-7 flex h-20 w-20 items-center justify-center rounded-full bg-[#EEF5F3]">
              <LoaderCircle className="animate-spin text-[#2F8578]" size={32} />
            </div>

            <p className="mb-3 text-sm uppercase tracking-[0.26em] text-[#2F8578]">
              processing
            </p>

            <h2 className="text-[2rem] font-medium tracking-[-0.04em]">
              Идёт анализ звонка
            </h2>

            <p className="mx-auto mt-5 max-w-[450px] text-base leading-8 text-[#585858]">
              Мы расшифровываем аудио, анализируем структуру диалога, проверяем
              соблюдение скрипта и формируем коучинговый отчёт.
            </p>

            <div className="mt-9 rounded-full bg-[#E8EFEC] p-2">
              <div className="h-2 w-2/3 rounded-full bg-[#2F8578]" />
            </div>

            <p className="mt-5 text-sm text-[#6C6C6C]">
              Файл:{" "}
              <span className="font-medium text-[#2A2A2A]">
                {file?.name || "—"}
              </span>
            </p>
          </div>
        </main>
      )}

      {screen === "report" && result && (
        <main className="relative z-10 mx-auto max-w-[1480px] px-6 py-10 md:px-10 xl:px-16">
          <WaveLineTop />
          <SpiralCompact className="right-[4%] top-[120px] hidden xl:block" />

          <div className="mb-8 flex flex-wrap items-start justify-between gap-4 pt-12">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#2F85781F] bg-white/55 px-4 py-2 text-sm text-[#2F8578] backdrop-blur-sm">
                <CheckCircle2 size={16} />
                Анализ завершён
              </div>

              <h1 className="text-4xl font-semibold tracking-[-0.05em] md:text-6xl">
                Отчёт по звонку
              </h1>

              <p className="mt-3 text-base text-[#5B5B5B]">
                Файл: <span className="font-medium">{result.filename}</span>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() =>
                  window.open(
                    `${API_BASE}/calls/${result.call_id}/download/pdf`,
                    "_blank"
                  )
                }
                className="inline-flex items-center gap-2 rounded-full border border-[#D9E4DF] bg-white/65 px-5 py-3 text-sm font-medium text-[#364236] transition hover:bg-white"
              >
                Скачать PDF
              </button>

              <button
                onClick={handleReset}
                className="inline-flex items-center gap-2 rounded-full border border-[#D9E4DF] bg-white/65 px-5 py-3 text-sm font-medium text-[#364236] transition hover:bg-white"
              >
                <ArrowLeft size={16} />
                Загрузить другой файл
              </button>
            </div>
          </div>

          {error && (
            <div className="mb-6 flex items-start gap-3 rounded-[24px] border border-[#E8D7D1] bg-[#FFF6F3] px-4 py-4 text-left text-sm leading-6 text-[#8A4E3B]">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <section className="grid grid-cols-1 gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <GlassCard>
              <CardLabel>summary</CardLabel>
              <CardTitle>Краткое резюме</CardTitle>

              <p className="mt-5 text-[15px] leading-8 text-[#4F4F4F]">
                {result.report.summary?.short_summary || "Нет данных."}
              </p>

              <div className="mt-7 rounded-[28px] bg-[#F5F1EA] p-5">
                <p className="text-sm uppercase tracking-[0.2em] text-[#5D7F73]">
                  результат звонка
                </p>
                <p className="mt-3 text-lg leading-8 text-[#242424]">
                  {result.report.summary?.result || "Нет данных."}
                </p>
              </div>
            </GlassCard>

            <GlassCard>
              <CardLabel>script</CardLabel>
              <CardTitle>Следование скрипту</CardTitle>

              <div className="mt-5 flex items-end gap-3">
                <span className="text-6xl font-semibold tracking-[-0.05em] text-[#2F8578]">
                  {score}
                </span>
                <span className="pb-2 text-sm text-[#7A7A7A]">/ 100</span>
              </div>

              <div className="mt-5 h-3 rounded-full bg-[#E7EFEB]">
                <div
                  className="h-3 rounded-full bg-[#2F8578]"
                  style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
                />
              </div>

              <div className="mt-7 space-y-5 text-sm text-[#545454]">
                <div>
                  <p className="mb-2 font-medium text-[#202020]">Пропущенные этапы</p>
                  {result.report.script_analysis?.missing_stages?.length ? (
                    <ul className="list-disc pl-5 leading-7">
                      {result.report.script_analysis.missing_stages.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>Пропущенные этапы не обнаружены.</p>
                  )}
                </div>

                <div>
                  <p className="mb-2 font-medium text-[#202020]">Нарушения</p>
                  {result.report.script_analysis?.violations?.length ? (
                    <ul className="list-disc pl-5 leading-7">
                      {result.report.script_analysis.violations.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p>Выраженных нарушений не обнаружено.</p>
                  )}
                </div>

                {result.report.script_analysis?.comment && (
                  <div className="rounded-[24px] bg-[#F5F1EA] p-4 leading-7">
                    {result.report.script_analysis.comment}
                  </div>
                )}
              </div>
            </GlassCard>
          </section>

          <section className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
            <GlassCard>
              <CardLabel>dialog stages</CardLabel>
              <CardTitle>Этапы диалога</CardTitle>

              <div className="mt-5 space-y-4">
                {result.report.dialog_stages?.length ? (
                  result.report.dialog_stages.map((stage, index) => (
                    <div
                      key={`${stage.stage}-${index}`}
                      className="rounded-[28px] bg-[#F5F1EA] p-5"
                    >
                      <div className="mb-3 inline-flex rounded-full border border-[#D8E4DE] bg-white/65 px-3 py-1 text-xs uppercase tracking-[0.18em] text-[#2F8578]">
                        {stage.stage || "Этап"}
                      </div>

                      <div className="space-y-2">
                        {stage.replicas?.length ? (
                          stage.replicas.map((replica, i) => (
                            <p
                              key={i}
                              className="text-sm leading-7 text-[#4E4E4E]"
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
                      className="rounded-[28px] border border-[#EADCD4] bg-[#FFF8F5] p-5"
                    >
                      <p className="text-sm uppercase tracking-[0.18em] text-[#A0614B]">
                        {mistake.type || "Ошибка"}
                      </p>
                      <p className="mt-3 text-sm leading-7 text-[#565656]">
                        {mistake.description || "Описание не указано."}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-[28px] bg-[#F2F7F3] p-5 text-sm text-[#4F6B50]">
                    Явные ошибки не обнаружены.
                  </div>
                )}
              </div>
            </GlassCard>
          </section>

          <section className="mt-6 grid grid-cols-1 gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <GlassCard>
              <CardLabel>recommendations</CardLabel>
              <CardTitle>Рекомендации</CardTitle>

              <div className="mt-5 space-y-4">
                {result.report.recommendations?.length ? (
                  result.report.recommendations.map((item, index) => (
                    <div key={index} className="rounded-[28px] bg-[#F5F1EA] p-5">
                      <p className="text-sm uppercase tracking-[0.18em] text-[#2F8578]">
                        Зона роста
                      </p>
                      <p className="mt-2 text-base font-medium text-[#232323]">
                        {item.zone_of_growth || "Не указано"}
                      </p>

                      <p className="mt-4 text-sm uppercase tracking-[0.18em] text-[#818181]">
                        Почему это важно
                      </p>
                      <p className="mt-2 text-sm leading-7 text-[#565656]">
                        {item.why_important || "Не указано"}
                      </p>

                      <p className="mt-4 text-sm uppercase tracking-[0.18em] text-[#818181]">
                        Что улучшать
                      </p>
                      <p className="mt-2 text-sm leading-7 text-[#565656]">
                        {item.what_to_improve || "Не указано"}
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

              <div className="mt-5 rounded-[28px] bg-[#F5F1EA] p-5">
                <p className="whitespace-pre-line text-sm leading-7 text-[#4D4D4D]">
                  {result.transcript || "Транскрипт отсутствует."}
                </p>
              </div>

              <button
                onClick={() => {
                  setScreen("processing");
                  setTimeout(() => setScreen("report"), 700);
                }}
                className="mt-5 inline-flex items-center gap-2 rounded-full border border-[#D8E4DE] bg-white/70 px-4 py-3 text-sm font-medium text-[#364236] transition hover:bg-white"
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

function Badge({ text }: { text: string }) {
  return (
    <span className="rounded-full border border-[#D9E4DF] bg-white/65 px-4 py-2">
      {text}
    </span>
  );
}

function GlobalDecor({ screen }: { screen: Screen }) {
  return (
    <>
      <div className="pointer-events-none absolute inset-0">
        <WaveLineTop />
        <WaveLineBottom />
      </div>

      {screen === "upload" && (
        <>
          <SpiralSingle className="right-[-30px] top-[15px] hidden 2xl:block" />
          <SpiralCompact className="left-[2%] bottom-[9%] hidden xl:block" />
        </>
      )}

      {screen === "report" && (
        <>
          <SpiralCompact className="left-[2%] top-[38%] hidden xl:block" />
          <SpiralSingle className="right-[-40px] bottom-[-20px] hidden 2xl:block" />
        </>
      )}
    </>
  );
}

function GlassCard({ children }: { children: React.ReactNode }) {
  return (
    <section className="rounded-[34px] border border-white/65 bg-white/58 p-6 shadow-[0_18px_60px_rgba(0,0,0,0.045)] backdrop-blur-md md:p-7">
      {children}
    </section>
  );
}

function CardLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-sm uppercase tracking-[0.24em] text-[#2F8578]">
      {children}
    </p>
  );
}

function CardTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mt-2 text-[2rem] font-semibold tracking-[-0.04em]">
      {children}
    </h2>
  );
}

function WaveLineTop() {
  return (
    <svg
      className="absolute left-0 top-0 w-full opacity-22"
      viewBox="0 0 1440 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M-20 46C29 46 29 31 78 31C127 31 127 46 176 46C225 46 225 31 274 31C323 31 323 46 372 46C421 46 421 31 470 31C519 31 519 46 568 46C617 46 617 31 666 31C715 31 715 46 764 46C813 46 813 31 862 31C911 31 911 46 960 46C1009 46 1009 31 1058 31C1107 31 1107 46 1156 46C1205 46 1205 31 1254 31C1303 31 1303 46 1352 46C1401 46 1401 31 1450 31"
        stroke="#2F8578"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function WaveLineBottom() {
  return (
    <svg
      className="absolute bottom-0 left-0 w-full opacity-10"
      viewBox="0 0 1440 180"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M-5 95C117 43 218 26 340 43C461 60 551 126 668 134C785 142 883 89 989 59C1092 31 1188 32 1299 67C1388 95 1464 112 1528 103"
        stroke="#2F8578"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function SpiralSingle({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute opacity-18 ${className}`}>
      <svg
        width="260"
        height="260"
        viewBox="0 0 260 260"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M130 130
             C130 110, 150 105, 162 116
             C176 128, 175 153, 154 166
             C126 183, 91 171, 75 139
             C57 101, 74 57, 120 41
             C176 21, 230 57, 240 117
             C250 180, 207 236, 136 246
             C56 256, -6 198, 5 113"
          stroke="#2F8578"
          strokeWidth="4"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}

function SpiralDouble({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute opacity-18 ${className}`}>
      <svg
        width="420"
        height="220"
        viewBox="0 0 420 220"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M91 112
             C91 89, 111 82, 124 94
             C138 106, 136 133, 115 145
             C87 161, 52 149, 37 119
             C20 85, 35 46, 76 31
             C126 12, 174 45, 183 99
             C192 156, 154 205, 93 213
             C24 222, -30 172, -20 98

             M328 112
             C328 89, 348 82, 361 94
             C375 106, 373 133, 352 145
             C324 161, 289 149, 274 119
             C257 85, 272 46, 313 31
             C363 12, 411 45, 420 99
             C429 156, 391 205, 330 213
             C261 222, 207 172, 217 98

             M183 99
             C205 88, 219 74, 228 48
             C237 22, 256 15, 281 16"
          stroke="#2F8578"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function SpiralCompact({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute opacity-16 ${className}`}>
      <svg
        width="140"
        height="140"
        viewBox="0 0 140 140"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M70 70
             C70 63, 77 60, 82 64
             C88 69, 88 79, 80 85
             C69 93, 54 91, 46 79
             C36 63, 41 42, 60 33
             C86 22, 115 35, 125 61
             C136 91, 119 121, 88 131"
          stroke="#2F8578"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}