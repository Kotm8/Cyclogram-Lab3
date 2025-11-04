import { useMemo, useState } from "react";
import type { CSSProperties, JSX } from "react";
import TaskTable from './TaskTable.tsx'
import RandomTaskGenerator from "./RandomTaskGenerator.tsx";
import { defaultArray, defaultRandomArray } from "../constants/constants.ts";

type TaskView = {
  id: number;
  status: "decoding" | "delayed" | "queued" | "executing" | "done" | "finished";
  first: boolean;
  taskLength: number;
  isCache: boolean;
  useBus: boolean;
  isDMA: boolean;
  busIndex?: number | null;
  decoded_at?: number | null;
};

type CacheView = { task: TaskView; time_left: number };

type DMAView = { task: TaskView; time_left: number };

type SentToCacheView = { bus: number; taskId: number };

type Tick = {
  id: number;
  buses: TaskView[];
  dma?: DMAView | null;
  cache?: CacheView | null;
  sentToCache?: SentToCacheView[] | null;
};

type Cyclogram = { ticks: Tick[] };

type RandomCyclogram = {
  ticks: Tick[];
  tickAmount1: number;
  tickAmount2: number;
};

export type InputTask = {
  id: number;
  length: number;
  isCache: boolean;
  useBus: boolean;
  isDMA: boolean;
}

export type RandomInputTask = {
  name: string
  chance: number;
  possibilities: RandomInputPossibilities[]
}
type RandomInputPossibilities = {
  chance: number;
  length: number;
}

type Block = {
  key: string;
  row: number;
  colStart: number;
  colEnd: number;
  className: string;
  label?: string | JSX.Element;
  style?: CSSProperties;
};

export default function App() {
  const [data, setData] = useState<Cyclogram>({ ticks: [] });
  const [taskTableData, setTaskTableData] = useState<InputTask[]>(defaultArray);
  const [RandomTableData, setRandomTableData] = useState<RandomInputTask[]>(defaultRandomArray);
  const CELL = 40;

  const dividerRows = [3, 8, 11, 14];
  const BUS_COUNT = 2;
  const BUS_ROWS = [dividerRows[0], dividerRows[1]];
  const DMA_ROW = dividerRows[2];
  const CACHE_ROW = dividerRows[3];
  const totalRows = Math.max(...dividerRows) + 1;

  const cols = data.ticks.length;

  const [cpuMHz, setCpuMHz] = useState(1000);
  const [sbMHz, setSbMHz] = useState(500);
  const [ramTiming, setRamTiming] = useState<[number, number, number, number]>([3, 0, 0, 0]);
  const [useTable, setUseTable] = useState(true);
  const [taskAmount, setTaskAmount] = useState(200);
  const [cacheChance1, setCacheChance1] = useState(75);
  const [cacheChance2, setCacheChance2] = useState(90);
  const [dmaChance, setDmaChance] = useState(65);
  const [cacheChance1Ticks, setCacheChance1Ticks] = useState(0);
  const [cacheChance2Ticks, setCacheChance2Ticks] = useState(0);

  const shadedLinesurl = `url("data:image/svg+xml,%3Csvg width='4' height='4' viewBox='0 0 6 6' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%239C92AC' fill-opacity='0.9' fill-rule='evenodd'%3E%3Cpath d='M4 0h2L0 6V4zM6 4v2H4z'/%3E%3C/g%3E%3C/svg%3E")`;

  const gridTemplateColumns = useMemo(
    () => `repeat(${Math.max(cols, 1)}, ${CELL}px)`,
    [cols]
  );


  const fetchData = () => {
    setData({ ticks: [] });
    const payload = {
      Tasks: taskTableData.map((task) => ({
        id: task.id,
        taskLength: task.length,
        isCache: task.isCache,
        useBus: task.useBus,
        isDMA: task.isDMA
      })),
      CPU_MHz: cpuMHz,
      SB_MHz: sbMHz,
      RamTiming: ramTiming[0] + ramTiming[1] + ramTiming[2] + ramTiming[3],
    };
    console.log(payload)

    fetch("http://127.0.0.1:8000/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((json: Cyclogram) => setData(json))
      .catch((e) => console.error(e));
  };

  const fetchRandomData = () => {
    setData({ ticks: [] });
    const payload = {
      TaskTable: defaultRandomArray.map(task => ({
        chance: task.chance,
        possibilities: task.possibilities.map(poss => ({
          chance: poss.chance,
          length: poss.length
        }))
      })),
      TaskAmount: taskAmount,
      CacheChance1: cacheChance1,
      CacheChance2: cacheChance2,
      CPU_MHz: cpuMHz,
      SB_MHz: sbMHz,
      RamTiming: ramTiming[0] + ramTiming[1] + ramTiming[2] + ramTiming[3],
      DMAChance: dmaChance,
    };
    console.log(payload)

    fetch("http://127.0.0.1:8000/run/random", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((json: RandomCyclogram) => {
        setCacheChance1Ticks(json.tickAmount1);
        setCacheChance2Ticks(json.tickAmount2);
        setData(json)
      })
      .catch((e) => console.error(e));
  };

  const ramTimingCalculator = () => {
    return (ramTiming[0] + ramTiming[1] + ramTiming[2] + ramTiming[3]) * Math.ceil(cpuMHz / sbMHz);
  };

  const blocks: Block[] = useMemo(() => {
    const out: Block[] = [];
    for (let c = 0; c < cols; c++) {
      const tick = data.ticks[c];
      if (!tick) continue;

      for (let b = 0; b < BUS_COUNT; b++) {
        const t = tick.buses?.[b];
        if (!t) continue;
        const span = 1;
        if (t.status === "decoding") {
          out.push({
            key: `bus-${b}-tick-${c}-task-${t.id}-1`,
            row: BUS_ROWS[b] - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `border-l-2 border-r-2 border-black`,
          });
          out.push({
            key: `bus-${b}-tick-${c}-task-${t.id}-2`,
            row: BUS_ROWS[b] - 2,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `rounded-t border-l-2 border-r-2 border-t-2 border-black`,
          });
          if (t.useBus) {
            out.push({
              key: `arrow-decoding-${b}-tick-${c}-task-${t.id}`,
              row: -1,
              colStart: -1,
              colEnd: -1,
              className: "text-black flex items-center justify-center font-bold z-50 pointer-events-none",
              label: (
                <span className="flex items-center space-x-1">
                  <span className="text-[24px] leading-none">↑</span>
                  <span className="text-[14px]">{t.id}</span>
                </span>
              ),
              style: {
                position: "absolute",
                top: `${(BUS_ROWS[b] - 3) * CELL + 10}px`,
                left: `${(c + 1) * CELL + 6}px`,
              },
            });
          }
          else {
            out.push({
              key: `arrow-decoding-${b}-tick-${c}-task-${t.id}`,
              row: -1,
              colStart: -1,
              colEnd: -1,
              className: "text-black flex items-center justify-center font-bold z-50 pointer-events-none",
              label: (
                <span className="flex items-center space-x-1">
                  <span className="text-[14px]">{t.id}</span>
                </span>
              ),
              style: {
                position: "absolute",
                top: `${(BUS_ROWS[b] - 3) * CELL + 10}px`,
                left: `${(c + 1) * CELL + 6}px`,
              },
            });
          }
          if (tick.sentToCache) {
            let offsety = 0
            tick.sentToCache.forEach(element => {
              if (b === element.bus) {

                out.push({
                  key: `arrow-decoding-${b}-tick-${c}-task-${t.id}-${element.taskId}`,
                  row: -1,
                  colStart: -1,
                  colEnd: -1,
                  className: "text-black flex items-center justify-center font-bold z-50 pointer-events-none",
                  label: (
                    <span className="flex items-center space-x-1">
                      <span className="text-[24px] leading-none">↑</span>
                      <span className="text-[14px]">{element.taskId}</span>
                    </span>
                  ),
                  style: {
                    position: "absolute",
                    top: `${(BUS_ROWS[b] - 3) * CELL + 10 - offsety}px`,
                    left: `${(c) * CELL + 8}px`,
                  },
                });
                offsety += CELL / 2 - 4
              }
            });
          }


        }
        else if (t.status === "finished") {

        }
        else if (t.status === "queued") {

        }
        else if (t.status === "delayed") {

        }
        else if (t.status === "done") {
          if (t.useBus) {
            if (t.first) {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `rounded-b border-l-2 border-r-2 border-b-2 border-black`,
                style: { backgroundImage: shadedLinesurl }
              });

            }
            else {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `rounded-br border-r-2 border-b-2 border-black`,
                style: { backgroundImage: shadedLinesurl }
              });

            }

          }
          else {
            if (t.first) {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `rounded-b border-l-2 border-r-2 border-b-2 border-black`,
              });

            }
            else {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `rounded-br border-r-2 border-b-2 border-black`,
              });

            }

          }
        }
        else {
          if (t.useBus) {
            if (t.first) {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `rounded-bl border-b-2 border-l-2 border-black`,
                style: { backgroundImage: shadedLinesurl }
              });
            }
            else {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: ` border-b-2 border-black`,
                style: { backgroundImage: shadedLinesurl }
              });
            }


          }
          else {
            if (t.first) {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `rounded-bl border-b-2 border-l-2  border-black`,
              });
            }
            else {
              out.push({
                key: `bus-${b}-tick-${c}-task-${t.id}`,
                row: BUS_ROWS[b],
                colStart: c + 1,
                colEnd: Math.min(cols + 1, c + 1 + span),
                className: `border-b-2 border-black`,
              });
            }
          }

        }
      }
      // @ts-ignore dma logic
      if (tick.dma?.time_left && tick.dma.time_left > 0 || (data.ticks[c - 1]?.dma?.time_left && data.ticks[c - 1].dma.time_left > 0)) {

        const span = 1;
        if (tick.dma?.time_left === (4 * Math.ceil(cpuMHz / sbMHz) - 1)) {
          out.push({
            key: `DMA-${c}`,
            row: DMA_ROW - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `rounded-l border-t-2 border-l-2 border-black`,
            style: { backgroundImage: shadedLinesurl }
          });
        }
        // @ts-ignore
        else if (tick.dma?.time_left > 0) {
          out.push({
            key: `DMA-${c}`,
            row: DMA_ROW - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `border-t-2 border-black`,
            style: { backgroundImage: shadedLinesurl }
          });
        }
        else {
          out.push({
            key: `DMA-${c}`,
            row: DMA_ROW - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `rounded-r border-t-2 border-r-2 border-black`,
            style: { backgroundImage: shadedLinesurl }
          });
        }

        if (tick.dma?.time_left === (4 * Math.ceil(cpuMHz / sbMHz) - 2)) {
          out.push({
            key: `DMA-decoding-tick-${c}-task-${data.ticks[c]?.dma?.task.id}`,
            row: -1,
            colStart: -1,
            colEnd: -1,
            className: "text-black flex items-center justify-center font-bold z-50 pointer-events-none",
            label: (
              <span className="flex items-center space-x-1">
                <span className="text-[14px]">{data.ticks[c]?.dma?.task.id}</span>
              </span>
            ),
            style: {
              position: "absolute",
              top: `${(DMA_ROW - 1) * CELL + 10}px`,
              left: `${(c + 1) * CELL + CELL / 2 - 10}px`,
              backgroundColor: "white",
              padding: "0px",
              borderRadius: "4px",
              width: "20px",
              height: "20px",
              lineHeight: "20px",
              textAlign: "center",
              fontSize: "16px",
            },
          });
        }
      }
      // @ts-ignore
      if (tick.cache?.time_left && tick.cache.time_left > 0 || (data.ticks[c - 1]?.cache?.time_left && data.ticks[c - 1].cache.time_left > 0)) {

        const span = 1;
        if (tick.cache?.time_left === (ramTimingCalculator() - 1)) {
          out.push({
            key: `cache-${c}`,
            row: CACHE_ROW - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `rounded-l border-t-2 border-l-2 border-black`,
            style: { backgroundImage: shadedLinesurl }
          });
        }
        // @ts-ignore
        else if (tick.cache?.time_left > 0) {
          out.push({
            key: `cache-${c}`,
            row: CACHE_ROW - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `border-t-2 border-black`,
            style: { backgroundImage: shadedLinesurl }
          });
        }
        else {
          out.push({
            key: `cache-${c}`,
            row: CACHE_ROW - 1,
            colStart: c + 1,
            colEnd: Math.min(cols + 1, c + 1 + span),
            className: `rounded-r border-t-2 border-r-2 border-black`,
            style: { backgroundImage: shadedLinesurl }
          });
        }

        if (tick.cache?.time_left === (ramTimingCalculator() - 2)) {
          out.push({
            key: `cache-decoding-tick-${c}-task-${data.ticks[c]?.cache?.task.id}`,
            row: -1,
            colStart: -1,
            colEnd: -1,
            className: "text-black flex items-center justify-center font-bold z-50 pointer-events-none",
            label: (
              <span className="flex items-center space-x-1">
                <span className="text-[14px]">{data.ticks[c]?.cache?.task.id}</span>
              </span>
            ),
            style: {
              position: "absolute",
              top: `${(CACHE_ROW - 1) * CELL + 10}px`,
              left: `${(c + 1) * CELL + CELL / 2 - 10}px`,
              backgroundColor: "white",
              padding: "0px",
              borderRadius: "4px",
              width: "20px",
              height: "20px",
              lineHeight: "20px",
              textAlign: "center",
              fontSize: "16px",
            },
          });
        }
      }
    }
    return out;
  }, [data, cols]);

  return (
    <div className="flex">
      <div className="p-4 space-y-3">
        <div className="flex items-center space-x-4">
          <button onClick={useTable ? fetchData : fetchRandomData}
            className="px-4 py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 transition">
            Fetch Data
          </button>
          <div>
            <label className="flex items-center space-x-2">
              <span>CPU-MHz:</span>
              <input
                type="number"
                placeholder={cpuMHz.toString()}
                value={cpuMHz}
                onChange={(e) => setCpuMHz(Number(e.target.value))}
                className="border rounded px-2 py-1 w-[100px]"
              />
            </label>
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <span>SB-MHz:</span>
              <input
                type="number"
                placeholder={sbMHz.toString()}
                value={sbMHz}
                onChange={(e) => setSbMHz(Number(e.target.value))}
                className="border rounded px-2 py-1 w-[100px]"
              />
            </label>
          </div>
          <div>
            <label className="flex items-center space-x-2">
              <span>Ram Timing:</span>
              <input
                type="text"
                value={ramTiming.join("-")}
                onChange={(e) => {
                  const parts = e.target.value.split("-").map((p) => Number(p));
                  if (parts.length === 4 && parts.every((n) => !isNaN(n))) {
                    setRamTiming(parts as [number, number, number, number]);
                  }
                }}
                className="border rounded px-2 py-1 w-[120px]"
              />
            </label>
          </div>

        </div>

        <div className="overflow-auto border min-h-[550px] max-h-[900px] min-w-[800px] max-w-[800px]">
          <div className="relative pl-12">
            <div
              className="relative"
              style={{
                display: "grid",
                gridTemplateRows: `repeat(${totalRows}, ${CELL}px)`,
              }}
            >
              {Array.from({ length: totalRows }).map((_, r) => {
                const isDivider = dividerRows.includes(r);
                const isBelowDivider = dividerRows.includes(r - 1);
                return (
                  <div key={`row-${r}`} className="grid" style={{ gridTemplateColumns }}>
                    {Array.from({ length: Math.max(cols, 1) }).map((_, c) => (
                      <div
                        key={`cell-${r}-${c}`}
                        style={{ width: CELL, height: CELL }}
                        className={[
                          "border border-gray-300",
                          isDivider ? "border-b-2 border-black" : "",
                          isBelowDivider ? "border-t-0" : "",
                        ].join(" ")}
                      />
                    ))}
                  </div>
                );
              })}

              {blocks.map((b) => (
                <div key={b.key}>
                  <div
                    className={`absolute flex items-center justify-center text-[10px] ${b.className}`}
                    style={{
                      top: `${b.row * CELL}px`,
                      left: `${(b.colStart - 1) * CELL}px`,
                      width: `${(b.colEnd - b.colStart) * CELL}px`,
                      height: `${CELL}px`,
                      ...b.style,
                    }}
                  >
                    {b.label}
                  </div>
                </div>
              ))}
              {dividerRows.map((dividerRow, idx) => (

                <div
                  key={`divider-line-${idx}`}
                  className="absolute bg-black/60"
                  style={{
                    top: `${(dividerRow) * CELL - 1}px`,
                    left: 0,
                    width: `calc(${Math.max(cols, 1)} * ${CELL}px)`,
                    height: "2px",
                  }}
                />
              ))}
              {dividerRows.map((dividerRow, idx) => {
                const labels = ["k1 ", "k2 ", "DMA", "kk "];
                return (
                  <div
                    key={`divider-label-${idx}`}
                    className="absolute text-sm font-semibold text-gray-700 pr-2"
                    style={{
                      top: `${(dividerRow - 0.5) * CELL}px`,
                      left: `-30px`,
                      height: `${CELL}px`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "flex-end",
                      width: "30px",
                    }}
                  >
                    {labels[idx] || ""}
                  </div>
                );
              })}


              <div
                className="absolute text-[10px]"
                style={{
                  top: `${totalRows * CELL}px`,
                  left: 0,
                  display: "grid",
                  gridTemplateColumns,
                  width: `calc(${Math.max(cols, 1)} * ${CELL}px)`,
                }}
              >
                {Array.from({ length: Math.max(cols, 1) }).map((_, i) => (
                  <div key={`label-${i}`} style={{ width: CELL }} className="text-center">
                    {i}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="">
        <div className="p-4 flex">
          <div>
            <span>Selectable:  </span>
            <select
              className="border rounded"
              value={useTable ? "true" : "false"}
              onChange={(e) => setUseTable(e.target.value === "true")}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </select>
          </div>

          {useTable ? null :
            <div className="ml-4">
              <div>
                <span>Task amount:  </span>
                <input
                  type="number"
                  className="w-16 border rounded px-1 text-center"
                  value={taskAmount}
                  onChange={(e) => setTaskAmount(Number(e.target.value))}
                />
                <span className="ml-4">Cache 1:  </span>
                <input
                  type="number"
                  className="w-16 border rounded px-1 text-center"
                  value={cacheChance1}
                  onChange={(e) => setCacheChance1(Number(e.target.value))}
                />
                <span >%</span>
                <span className="ml-4">Cache 2:  </span>
                <input
                  type="number"
                  className="w-16 border rounded px-1 text-center"
                  value={cacheChance2}
                  onChange={(e) => setCacheChance2(Number(e.target.value))}
                />
                <span >%</span>
              </div>

              <span >DMA:  </span>
              <input
                type="number"
                className="w-16 border rounded px-1 text-center"
                value={dmaChance}
                onChange={(e) => setDmaChance(Number(e.target.value))}
              />
              <span >%</span>
            </div>
          }

        </div>
        <div className="max-h-[550px] min-w-[700px] overflow-auto">
          {useTable ? <TaskTable data={taskTableData} setData={setTaskTableData} /> : <RandomTaskGenerator data={RandomTableData} setData={setRandomTableData} />}
        </div>
        {(!useTable && cacheChance1Ticks !== 0) ?
          <div className="ml-4">
            <span>Количество тактов при {cacheChance1}%: <strong>{cacheChance1Ticks}</strong> Времени затраченное (ms): {(cacheChance1Ticks / (cpuMHz * 1000)).toFixed(5)} <br /></span>
            <span>Количество тактов при {cacheChance2}%: <strong>{cacheChance2Ticks}</strong> Времени затраченное (ms): {(cacheChance2Ticks / (cpuMHz * 1000)).toFixed(5)}<br /></span>

            <span>Отношение тактов кэш попадания {cacheChance1}% к {cacheChance2}% =  <strong>{(cacheChance1Ticks / cacheChance2Ticks).toFixed(2)}</strong></span>
          </div>
          : null}
      </div>
    </div>
  );
}
