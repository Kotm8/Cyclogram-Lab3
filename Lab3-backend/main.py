from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import copy
import math
import random
from fastapi.middleware.cors import CORSMiddleware
import sys
import json

sys.setrecursionlimit(1000000)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Task:
    id: int
    taskLength: int
    isCache: bool
    useBus: bool
    status: str
    busIndex: Optional[int]
    first: bool
    decoded_at: Optional[int]
    
    def __init__(self, id, length, cacheBool, busBool):
        self.id = id
        self.taskLength = length
        self.isCache = cacheBool
        self.useBus = busBool
        self.status = "queued"      
        self.busIndex = None 
        self.first = True

class TaskInCache:
    def __init__(self, Task, timeLeftinCache):
        self.Task = Task
        self.timeLeftinCache = timeLeftinCache

class TaskView(BaseModel):
    id: int
    status: str
    first: bool
    taskLength: int
    isCache: bool
    useBus: bool
    busIndex: Optional[int] = None
    decoded_at: Optional[int] = None
    
class CacheView(BaseModel):
    task: TaskView
    time_left: int
    
class DMAView(BaseModel):
    task: TaskView
    time_left: int
    
    
class sentToCacheView(BaseModel):
    bus: int
    taskId: int
    
class Tick(BaseModel):
    id: int
    buses: List[TaskView] 
    cache: Optional[List[CacheView]] = None
    sentToCache: Optional[List[sentToCacheView]] = None

class Cyclogram(BaseModel):
    ticks: List[Tick]

class CyclogramRandom(BaseModel):
    ticks: List[Tick]
    tickAmount1: int
    tickAmount2: int

class TaskInput(BaseModel):
    id: int
    taskLength: int
    isCache: bool
    useBus: bool
    
class RunParameters(BaseModel):
    Tasks: List[List[TaskInput]]
    CPU_MHz: int
    SB_MHz: int
    RamTiming: int

class RandomInputPossibilities(BaseModel):
    chance: int
    length: int
  
class RandomInputTask(BaseModel):
    chance: int
    possibilities: List[RandomInputPossibilities]
    
class RunRandomParameters(BaseModel):
    TaskTable: List[RandomInputTask]
    TaskAmount: int
    CacheChance1: int
    CacheChance2: int
    CPU_MHz: int
    SB_MHz: int
    RamTiming: int

  
BUS_COUNT = 3

buses = [[] for _ in range(BUS_COUNT)]
busesQueue = [[] for _ in range(BUS_COUNT)]
sentToCacheTick = [[] for _ in range(BUS_COUNT)]
cacheController = [[] for _ in range(BUS_COUNT)]
cacheQueue = [[] for _ in range(BUS_COUNT)]

print(buses, busesQueue, sentToCacheTick, cacheController, cacheQueue)
ramTiming = 3

CPU_MHz = 1000
SB_MHz = 500

mult = 2
clock = 0

isBusUsed = False
wasBusFreed = False
BaseQueue: List[List[Task]] = [[
    Task( 1, 2, True , True ),
    Task( 2, 2, True , False ),  
    Task( 3, 1, False, False),
    Task( 4, 2, False, True ),
    Task( 5, 1, True , True ),
    Task( 6, 2, True , False),
    Task( 7, 1, False, False),
    Task( 8, 2, True , True ),
],[
    Task( 1, 1, True , False),
    Task( 2, 2, False, True ),  
    Task( 3, 1, True , True ),
    Task( 4, 2, True , True ),
    Task( 5, 2, False, False),
    Task( 6, 1, True , False),
    Task( 7, 2, True , True ),
],[
    Task( 1, 1, False, True ),
    Task( 2, 2, True , False),  
    Task( 3, 1, False, False),
    Task( 4, 2, True , True ),
    Task( 5, 1, True , False),
    Task( 6, 2, False, True ),
    Task( 7, 1, True , True ),
]]

mainQueue: List[List[Task]] = copy.deepcopy(BaseQueue)

def NewTask(i):
    global mainQueue
    global sentToCacheTick
        
    if buses[i] and buses[i][-1].status in ("decoding", "executing", "delayed"):
        return
    
    if busesQueue[i]:
        next_task = busesQueue[i].pop(0)
        next_task.busIndex = i
    else:
        if not mainQueue[i]:
            return
        
        next_task = mainQueue[i].pop(0)
        next_task.busIndex = i
        
        
        if not next_task.isCache:
            next_task.cache_request_time = clock
            cacheQueue[i].append(next_task)
            sentToCacheTick[i].append([i, next_task.id])
            NewTaskOnlyForBus(i)
            return
        
    next_task.status = "decoding"
    next_task.decoded_at = clock
    buses[i].append(next_task)
    
def NewTaskOnlyForBus(busIndex):
    if buses[busIndex] and buses[busIndex][-1].status in ("decoding", "executing", "delayed"):
        return
    
    if busesQueue[busIndex]:
        next_task = busesQueue[busIndex].pop(0)
        next_task.busIndex = busIndex
    else:
        if not mainQueue[busIndex]:
            return
        next_task = mainQueue[busIndex].pop(0)
        next_task.busIndex = busIndex
    
        
        if not next_task.isCache:
            next_task.cache_request_time = clock
            cacheQueue[busIndex].append(next_task)
            sentToCacheTick[busIndex].append([busIndex, next_task.id])
            NewTaskOnlyForBus(busIndex)
            return
        
    next_task.status = "decoding"
    next_task.decoded_at = clock         
    buses[busIndex].append(next_task)

def DoDecodedTasks(i): 
    global isBusUsed
    global wasBusFreed
    
    if not buses[i]:
        return
    last = buses[i][-1]

    if last.status == "decoding":
        if getattr(last, "decoded_at", -1) < clock:
            last.status = "executing"
            if last.useBus:
                last.taskLength *= mult
                if isBusUsed:
                    last.status = "delayed"
                else:
                    if (checkIfPriorityBus(i)):
                        isBusUsed = True
                        last.taskLength -= 1
                    else:
                        last.status = "delayed"
            else:
                last.taskLength -= 1
                if last.taskLength <= 0:
                    last.status = "done"
        buses[i].append(last)

    elif last.status == "delayed":
        if not isBusUsed:
            if (checkIfPriorityBus(i)):
                isBusUsed = True
                last.status = "executing"
                last.taskLength -= 1
        buses[i].append(last)

    elif last.status == "executing":
        if last.useBus:
            last.taskLength -= 1
            if last.taskLength <= 0:
                last.status = "done"
                wasBusFreed = True
                
        else:
            last.taskLength -= 1
            if last.taskLength <= 0:
                last.status = "done"
        last.first = False
        buses[i].append(last)
    elif last.status == "done":
        last.status = "finished"
        buses[i].append(last)
        
def checkIfPriorityBus(busIndex):
    my_task = buses[busIndex][-1]
    my_time = getattr(my_task, "decoded_at", -1)

    for i in range(BUS_COUNT):
        if i == busIndex:
            continue
        if not buses[i]:
            continue
        other = buses[i][-1]
        other_time = getattr(other, "decoded_at", -1)

        if other_time > my_time and other.status in ("delayed"):
            return False

    for i in range(BUS_COUNT):
        if i == busIndex:
            continue
        if not cacheQueue[i]:
            continue
        other = cacheQueue[i][-1]
        other_time = getattr(other, "cache_request_time", -1)

        if other_time > my_time and not(buses[i][-1].status in ("executing", "done")):
            return False

    return True

def checkIfPriorityQueue(busIndex):
    my_task = cacheQueue[busIndex][0]
    my_time = getattr(my_task, "cache_request_time", -1)
    
    for i in range(BUS_COUNT):
        if i == busIndex:
            continue
        if not buses[i]:
            continue

        other = buses[i][-1]
        other_time = getattr(other, "decoded_at", -1)

        if other.status in ("delayed"):
            if other_time > my_time:
                return False

    for i in range(BUS_COUNT):
        if i == busIndex:
            continue
        if not cacheQueue[i]:
            continue

        other = cacheQueue[i][0]
        other_time = getattr(other, "cache_request_time", -1)

        if other_time > my_time and not(buses[i][-1].status in ("executing", "done")):
            return False

    return True


def CacheProgressor(i):
    global isBusUsed
    global wasBusFreed
    
    if cacheController[i] and cacheController[i][-1] and cacheController[i][-1].timeLeftinCache > 0:
        current = cacheController[i][-1]
        current.timeLeftinCache -= 1
        if current.timeLeftinCache == 0:
            wasBusFreed = True
            t = current.Task
            t.isCache = True
            t.status = "queued"
            busesQueue[t.busIndex].append(t)
            return
        return

    if cacheQueue[i] and not isBusUsed:
        if checkIfPriorityQueue(i):
            task = cacheQueue[i].pop(0)
            cacheController[i].append(TaskInCache(task, ramTiming * mult - 1))
            isBusUsed = True
        
        
def tick():
    global isBusUsed
    global wasBusFreed
    global sentToCacheTick
    global cacheQueue
    sentToCacheTick = [[] for _ in range(BUS_COUNT)]
    
    for i in range(len(buses)):
        NewTask(i)
    for i in range(len(buses)):
        NewTask(i)
        DoDecodedTasks(i)
        CacheProgressor(i)
    if (wasBusFreed):
        isBusUsed = False
    wasBusFreed = False 
    
    
    
def work_remaining():
    
    if any(len(q) > 0 for q in mainQueue):
        return True
    if any(len(q) > 0 for q in busesQueue):
        return True
    if any(len(q) > 0 for q in cacheQueue):
        return True
    for i in range(BUS_COUNT):
        if cacheController[i]:
            last = cacheController[i][-1]
            if last.timeLeftinCache > 0:
                return True
    for bus in buses:
        if bus and bus[-1].status in ("queued", "decoding", "executing", "delayed"):
            return True
    return False

def snapshot(clock: int) -> Tick:
    global sentToCacheTick 
    buses_views: List[TaskView] = []
    for lane in buses:
        if lane:
            t = lane[-1]
            buses_views.append(TaskView(
                id=t.id,
                status=t.status,
                first=t.first,
                taskLength=t.taskLength,
                isCache=t.isCache,
                useBus=t.useBus,
                busIndex=t.busIndex,
                decoded_at=getattr(t, "decoded_at", None)
            ))
    
    cache_view: List[CacheView] = []
    for lane in cacheController:
        if lane and lane[-1]:
            c = lane[-1]
            cache_view.append(CacheView(
                task=TaskView(
                    id=c.Task.id,
                    status=c.Task.status,
                    first=c.Task.first,
                    taskLength=c.Task.taskLength,
                    isCache=c.Task.isCache,
                    useBus=c.Task.useBus,
                    busIndex=c.Task.busIndex,
                    decoded_at=getattr(c.Task, "decoded_at", None)
                ),
                time_left=c.timeLeftinCache
            ))
    sent = None
    for lane in sentToCacheTick:
        if lane:
            sent = [sentToCacheView(bus=bus_idx, taskId=task_id)
                    for bus_idx, task_id in lane]

    return Tick(id=clock, buses=buses_views, cache=cache_view, sentToCache=sent)



def generateTasks(randomTable, taskAmount, CacheChance1, CacheChance2):
    tasks1 = [[] for _ in range(BUS_COUNT)]
    tasks2 = [[] for _ in range(BUS_COUNT)]
    for busIndex in range(BUS_COUNT):
        for i in range(1, taskAmount+1):
            random1 = random.random() * 100 // 1
            random2 = random.random() * 100 // 1
            random3 = random.random() * 100 // 1
            if (random1 < randomTable[0].chance): # Моделирование динамики объекта
                if (random2 < randomTable[0].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[0].possibilities[0].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[0].possibilities[0].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[0].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[0].length, False, False))
                elif ((random2 < (randomTable[0].possibilities[0].chance + randomTable[0].possibilities[1].chance))):
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[0].possibilities[1].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[0].possibilities[1].length, False, False))
                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[1].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[1].length, False, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[0].possibilities[2].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[0].possibilities[2].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[2].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[2].length, False, False))
            elif (random1 < (randomTable[0].chance + randomTable[1].chance)): # Моделирование систем объекта
                if (random2 < randomTable[1].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[1].possibilities[0].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[1].possibilities[0].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[1].possibilities[0].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[1].possibilities[0].length, False, False))
                elif (random2 < (randomTable[1].possibilities[0].chance + randomTable[1].possibilities[1].chance)):
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[1].possibilities[1].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[1].possibilities[1].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[1].possibilities[1].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[1].possibilities[1].length, False, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[1].possibilities[2].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[1].possibilities[2].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[2].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[0].possibilities[2].length, False, False))

            elif (random1 < (randomTable[0].chance + randomTable[1].chance + randomTable[2].chance)): # Управление объектом
                if (random2 < randomTable[2].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[2].possibilities[0].length, True, True))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[2].possibilities[0].length, False, True))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[2].possibilities[0].length, True, True))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[2].possibilities[0].length, False, True))
                else:
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[2].possibilities[1].length, True, True))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[2].possibilities[1].length, False, True))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[2].possibilities[1].length, True, True))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[2].possibilities[1].length, False, True))
            else:                                                                                   # Диспетчеризация вычислительного процесса
                if (random2 < randomTable[3].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[3].possibilities[0].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[3].possibilities[0].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[3].possibilities[0].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[3].possibilities[0].length, False, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1[busIndex].append(Task(i, randomTable[3].possibilities[1].length, True, False))
                    else: 
                        tasks1[busIndex].append(Task(i, randomTable[3].possibilities[1].length, False, False))

                    if(random3 < CacheChance2):
                        tasks2[busIndex].append(Task(i, randomTable[3].possibilities[1].length, True, False))
                    else: 
                        tasks2[busIndex].append(Task(i, randomTable[3].possibilities[1].length, False, False))
    return (tasks1, tasks2)
def reset_state():
    global buses, busesQueue, cacheQueue, cacheController, sentToCacheTick
    global isBusUsed, wasBusFreed, clock
    
    buses = [[] for _ in range(BUS_COUNT)]
    busesQueue = [[] for _ in range(BUS_COUNT)]
    sentToCacheTick = [[] for _ in range(BUS_COUNT)]
    cacheController = [[] for _ in range(BUS_COUNT)]
    cacheQueue = [[] for _ in range(BUS_COUNT)]
    
    isBusUsed = False
    wasBusFreed = False
    clock = 0
    
@app.get("/run", response_model=Cyclogram)
def run_all():
    global mainQueue
    global clock
    global BaseQueue
    clock = 0
    mainQueue = copy.deepcopy(BaseQueue)
    ticks: List[Tick] = []
    reset_state()
    
    
    while work_remaining():
        tick()
        print(clock)
        ticks.append(snapshot(clock))
        clock += 1
    result = Cyclogram(ticks=ticks)

    with open("cyclogram_output.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=4, ensure_ascii=False)

    print("Saved ticks → cyclogram_output.json")

    
    return Cyclogram(ticks=ticks)


@app.post("/run", response_model=Cyclogram)
def run_parameters(params: RunParameters):
    print(params)
    global mainQueue, clock, BaseQueue, CPU_MHz, SB_MHz, ramTiming, mult
    CPU_MHz = params.CPU_MHz
    SB_MHz = params.SB_MHz
    mult = math.ceil(CPU_MHz/SB_MHz)
    ramTiming = params.RamTiming
    reset_state()
    
    mainQueue = [
        [Task(t.id, t.taskLength, t.isCache, t.useBus) for t in lane]
        for lane in params.Tasks
    ]
    clock = 0
    
    ticks: List[Tick] = []

    while work_remaining() and clock < 5000:
        tick()
        ticks.append(snapshot(clock))
        clock += 1
        
    result = Cyclogram(ticks=ticks)

    with open("cyclogram_output.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=4, ensure_ascii=False)

    print("Saved ticks → cyclogram_output.json")
    
    return Cyclogram(ticks=ticks)
    
@app.post("/run/random", response_model=CyclogramRandom)
def run_parameters_random(params: RunRandomParameters):
    print(params)
    global mainQueue, clock, BaseQueue, CPU_MHz, SB_MHz, ramTiming, mult
    CPU_MHz = params.CPU_MHz
    SB_MHz = params.SB_MHz
    mult = math.ceil(CPU_MHz/SB_MHz)
    ramTiming = params.RamTiming
    tasks1, tasks2 = generateTasks(params.TaskTable, params.TaskAmount, params.CacheChance1, params.CacheChance2)
    
    reset_state()
    clock = 0
    mainQueue = copy.deepcopy(tasks1)  
    ticks: List[Tick] = []
    while work_remaining() and clock < 5000:
        tick()
        ticks.append(snapshot(clock))
        clock += 1
    tickAmount1 = clock
    
    reset_state()
    clock = 0
    mainQueue = copy.deepcopy(tasks2)  
    ticks: List[Tick] = []
    while work_remaining() and clock < 5000:
        tick()
        ticks.append(snapshot(clock))
        clock += 1
    tickAmount2 = clock
    print(tickAmount1, tickAmount2)
    result = Cyclogram(ticks=ticks)

    with open("cyclogram_output.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=4, ensure_ascii=False)

    print("Saved ticks → cyclogram_output.json")
    return CyclogramRandom(ticks=ticks, tickAmount1=tickAmount1, tickAmount2=tickAmount2)

run_all()