import type {InputTask, RandomInputTask} from "../src/App"

export const defaultArray: InputTask[] = [
  { id: 1,  length: 1, isCache: false, useBus: false, isDMA: false },
  { id: 2,  length: 2, isCache: true,  useBus: true,  isDMA: false },
  { id: 3,  length: 4, isCache: false, useBus: false, isDMA: true  },
  { id: 4,  length: 2, isCache: false, useBus: true,  isDMA: false },
  { id: 5,  length: 1, isCache: false, useBus: true,  isDMA: false },
  { id: 6,  length: 1, isCache: true,  useBus: false, isDMA: false },
  { id: 7,  length: 4, isCache: false, useBus: false, isDMA: true  },
  { id: 8,  length: 1, isCache: true,  useBus: true,  isDMA: false },
  { id: 9,  length: 4, isCache: false, useBus: false, isDMA: true  },
  { id: 10, length: 2, isCache: true,  useBus: false, isDMA: false },
  { id: 11, length: 1, isCache: false, useBus: false, isDMA: false },
  { id: 12, length: 2, isCache: true,  useBus: true,  isDMA: false },
  { id: 13, length: 1, isCache: false, useBus: true,  isDMA: false },
  { id: 14, length: 4, isCache: false, useBus: false, isDMA: true  },
  { id: 15, length: 2, isCache: true,  useBus: false, isDMA: false },
  { id: 16, length: 1, isCache: false, useBus: false, isDMA: false },
  { id: 17, length: 2, isCache: false, useBus: true,  isDMA: false },
  { id: 18, length: 2, isCache: true,  useBus: true,  isDMA: false },
];

export const defaultRandomArray: RandomInputTask[] = [
  { name: "Моделирование динамики объекта", chance: 30, possibilities: [
    {chance: 70, length: 5},
    {chance: 15, length: 2},
    {chance: 15, length: 1},
  ]},
  { name: "Моделирование систем объекта", chance: 25, possibilities: [
    {chance: 70, length: 2},
    {chance: 20, length: 5},
    {chance: 10, length: 1},
  ]},
  { name: "Управление объектом", chance: 15, possibilities: [
    {chance: 80, length: 2},
    {chance: 20, length: 1},
  ]},
  { name: "Диспетчеризация вычислительного процесса", chance: 30, possibilities: [
    {chance: 60, length: 2},
    {chance: 40, length: 1},
  ]},
];