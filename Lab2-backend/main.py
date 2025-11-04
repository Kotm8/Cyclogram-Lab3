from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import copy
import math
import random
from fastapi.middleware.cors import CORSMiddleware
import sys

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
    isDMA: bool
    status: str
    busIndex: Optional[int]
    first: bool
    decoded_at: Optional[int]
    
    def __init__(self, id, length, cacheBool, busBool, dmaBool):
        self.id = id
        self.taskLength = length
        self.isCache = cacheBool
        self.useBus = busBool
        self.isDMA = dmaBool
        self.status = "queued"      
        self.busIndex = None 
        self.first = True

class TaskInCache:
    def __init__(self, Task, timeLeftinCache):
        self.Task = Task
        self.timeLeftinCache = timeLeftinCache
        
class TaskInDMA:
    def __init__(self, Task, timeLeftinDMA):
        self.Task = Task
        self.timeLeftinDMA = timeLeftinDMA


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
    dma: Optional[DMAView] = None
    cache: Optional[CacheView] = None
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
    isDMA: bool
    
class RunParameters(BaseModel):
    Tasks: List[TaskInput]
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
    DMAChance: int

  
BUS_COUNT = 2

buses = [[] for _ in range(BUS_COUNT)]
busesQueue = [[] for _ in range(BUS_COUNT)]
sentToCacheTick = []
cacheController = []
cacheQueue = []
DMAQueue = []
DMAController = []

ramTiming = 3
dmaLength = 4

CPU_MHz = 1000
SB_MHz = 400

mult = round(CPU_MHz/SB_MHz)
clock = 0

isBusUsed = False
wasBusFreed = False
BaseQueue = [
    Task( 1, 1, False, False, False),
    Task( 2, 2, True , True , False),  
    Task( 3, 4, False, False, True ),
    Task( 4, 2, False, True , False),
    Task( 5, 1, False, True , False),
    Task( 6, 1, True , False, False),
    Task( 7, 4, False, False, True ),
    Task( 8, 1, True , True , False),
    Task( 9, 4, False, False, True ),
    Task(10, 2, True , False, False),
    Task(11, 1, False, False, False),
    Task(12, 2, True , True , False),
    Task(13, 1, False, True , False),
    Task(14, 4, False, False, True ),
    Task(15, 2, True , False, False),
    Task(16, 1, False, False, False),
    Task(17, 2, False, True , False),
    Task(18, 2, True , True , False),
]

mainQueue = copy.deepcopy(BaseQueue)

def NewTask():
    global mainQueue
    global sentToCacheTick
    for i in range(len(buses)):
        
        if buses[i] and buses[i][-1].status in ("decoding", "executing", "delayed"):
            continue
        
        if busesQueue[i]:
            next_task = busesQueue[i].pop(0)
            next_task.busIndex = i
        else:
            if not mainQueue:
                continue
            
            next_task = mainQueue.pop(0)
            next_task.busIndex = i
            
            
            if next_task.isDMA:
                next_task.decoded_at = clock
                DMAQueue.append(next_task)
                sentToCacheTick.append([i, next_task.id])
                NewTaskOnlyForBus(i)
                continue
            
            if not next_task.isCache:
                cacheQueue.append(next_task)
                sentToCacheTick.append([i, next_task.id])
                NewTaskOnlyForBus(i)
                continue
            
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
        if not mainQueue:
            return
        next_task = mainQueue.pop(0)
        next_task.busIndex = busIndex
    
        if next_task.isDMA:
            next_task.decoded_at = clock
            DMAQueue.append(next_task)
            sentToCacheTick.append([busIndex, next_task.id])
            NewTaskOnlyForBus(busIndex)
            return
        
        if not next_task.isCache:
            cacheQueue.append(next_task)
            sentToCacheTick.append([busIndex, next_task.id])
            NewTaskOnlyForBus(busIndex)
            return
        
    next_task.status = "decoding"
    next_task.decoded_at = clock         
    buses[busIndex].append(next_task)

def DoDecodedTasks(): 
    global isBusUsed
    global wasBusFreed
    for i in range(len(buses)):
        if not buses[i]:
            continue
        last = buses[i][-1]

        if last.status == "decoding":
            if getattr(last, "decoded_at", -1) < clock:
                last.status = "executing"
                if last.useBus:
                    last.taskLength *= mult
                    if isBusUsed:
                        last.status = "delayed"
                    else:
                        if (checkIfPriority(i)):
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
                if (checkIfPriority(i)):
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
            
def DoDMATasks():
    global isBusUsed
    global wasBusFreed
    
    if DMAController and DMAController[-1] and DMAController[-1].timeLeftinDMA > 0:
        current = DMAController[-1]
        current.timeLeftinDMA -= 1
        if current.timeLeftinDMA == 0:
            wasBusFreed = True
            return
        return

    if DMAQueue and not isBusUsed:
        DMAController.append(TaskInDMA(DMAQueue.pop(0), dmaLength * mult - 1))
        isBusUsed = True
        
def checkIfPriority(busIndex):
    if (DMAQueue):
        if (DMAQueue[0].decoded_at <= buses[busIndex][-1].decoded_at):
            return False
    if (busIndex == len(buses)-1):
        return True
    for i in range(busIndex, len(buses)):
        last = buses[i][-1]
        if last.decoded_at < buses[busIndex][-1].decoded_at and last.status == "delayed" and buses[busIndex][-1].status == "delayed":
            return False
    return True

def CacheProgressor():
    global isBusUsed
    global wasBusFreed
    if cacheController and cacheController[-1] and cacheController[-1].timeLeftinCache > 0:
        current = cacheController[-1]
        current.timeLeftinCache -= 1
        if current.timeLeftinCache == 0:
            wasBusFreed = True
            t = current.Task
            t.isCache = True
            t.status = "queued"
            busesQueue[t.busIndex].insert(0, t)
            return
        return

    if cacheQueue and not isBusUsed:
        cacheController.append(TaskInCache(cacheQueue.pop(0), ramTiming * mult - 1))
        isBusUsed = True
        
        
def tick():
    global isBusUsed
    global wasBusFreed
    global sentToCacheTick
    global cacheQueue
    sentToCacheTick = []
    NewTask()
    DoDecodedTasks()
    DoDMATasks()
    CacheProgressor()
    if (wasBusFreed):
        isBusUsed = False
    wasBusFreed = False 
    
    
def work_remaining():
    if mainQueue:
        return True
    if any(bq for bq in busesQueue):
        return True
    if cacheQueue:
        return True
    if cacheController and cacheController[-1] and cacheController[-1].timeLeftinCache > 0:
        return True
    if DMAQueue:
        return True
    if DMAController and DMAController[-1] and DMAController[-1].timeLeftinDMA > 0:
        return True
    if any(bus and bus[-1].status in ("queued", "decoding", "executing", "delayed") for bus in buses):
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

    DMA_view = None
    if DMAController and DMAController[-1]:
        c = DMAController[-1]
        DMA_view = DMAView(
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
            time_left=c.timeLeftinDMA
        )
    
    cache_view = None
    if cacheController and cacheController[-1]:
        c = cacheController[-1]
        cache_view = CacheView(
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
        )
    sent = None
    if sentToCacheTick:
        sent = [sentToCacheView(bus=bus_idx, taskId=task_id)
                for bus_idx, task_id in sentToCacheTick]

    return Tick(id=clock, buses=buses_views, cache=cache_view, dma=DMA_view, sentToCache=sent)


def generateTasks(randomTable, taskAmount, CacheChance1, CacheChance2, DMAChance):
    tasks1 = []
    tasks2 = []
    for i in range(1, taskAmount+1):
        random1 = random.random() * 100 // 1
        random2 = random.random() * 100 // 1
        random3 = random.random() * 100 // 1
        random4 = random.random() * 100 // 1
        if (random4 < DMAChance):
            tasks1.append(Task(i, dmaLength, False, False, True))
            tasks2.append(Task(i, dmaLength, False, False, True))
        else:
            if (random1 < randomTable[0].chance): # Моделирование динамики объекта
                if (random2 < randomTable[0].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[0].possibilities[0].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[0].possibilities[0].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[0].possibilities[0].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[0].possibilities[0].length, False, False, False))
                elif ((random2 < (randomTable[0].possibilities[0].chance + randomTable[0].possibilities[1].chance))):
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[0].possibilities[1].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[0].possibilities[1].length, False, False, False))
                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[0].possibilities[1].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[0].possibilities[1].length, False, False, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[0].possibilities[2].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[0].possibilities[2].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[0].possibilities[2].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[0].possibilities[2].length, False, False, False))
            elif (random1 < (randomTable[0].chance + randomTable[1].chance)): # Моделирование систем объекта
                if (random2 < randomTable[1].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[1].possibilities[0].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[1].possibilities[0].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[1].possibilities[0].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[1].possibilities[0].length, False, False, False))
                elif (random2 < (randomTable[1].possibilities[0].chance + randomTable[1].possibilities[1].chance)):
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[1].possibilities[1].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[1].possibilities[1].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[1].possibilities[1].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[1].possibilities[1].length, False, False, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[1].possibilities[2].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[1].possibilities[2].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[0].possibilities[2].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[0].possibilities[2].length, False, False, False))

            elif (random1 < (randomTable[0].chance + randomTable[1].chance + randomTable[2].chance)): # Управление объектом
                if (random2 < randomTable[2].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[2].possibilities[0].length, True, True, False))
                    else: 
                        tasks1.append(Task(i, randomTable[2].possibilities[0].length, False, True, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[2].possibilities[0].length, True, True, False))
                    else: 
                        tasks2.append(Task(i, randomTable[2].possibilities[0].length, False, True, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[2].possibilities[1].length, True, True, False))
                    else: 
                        tasks1.append(Task(i, randomTable[2].possibilities[1].length, False, True, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[2].possibilities[1].length, True, True, False))
                    else: 
                        tasks2.append(Task(i, randomTable[2].possibilities[1].length, False, True, False))
            else:                                                                                   # Диспетчеризация вычислительного процесса
                if (random2 < randomTable[3].possibilities[0].chance):
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[3].possibilities[0].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[3].possibilities[0].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[3].possibilities[0].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[3].possibilities[0].length, False, False, False))
                else:
                    if(random3 < CacheChance1):
                        tasks1.append(Task(i, randomTable[3].possibilities[1].length, True, False, False))
                    else: 
                        tasks1.append(Task(i, randomTable[3].possibilities[1].length, False, False, False))

                    if(random3 < CacheChance2):
                        tasks2.append(Task(i, randomTable[3].possibilities[1].length, True, False, False))
                    else: 
                        tasks2.append(Task(i, randomTable[3].possibilities[1].length, False, False, False))
    return (tasks1, tasks2)

@app.get("/run", response_model=Cyclogram)
def run_all():
    global mainQueue
    global clock
    global BaseQueue
    clock = 0
    mainQueue = copy.deepcopy(BaseQueue)
    ticks: List[Tick] = []
    
    
    while work_remaining():
        tick()
        ticks.append(snapshot(clock))
        clock += 1
    return Cyclogram(ticks=ticks)

@app.post("/run", response_model=Cyclogram)
def run_parameters(params: RunParameters):
    print(params)
    global mainQueue, clock, BaseQueue, CPU_MHz, SB_MHz, ramTiming, mult
    CPU_MHz = params.CPU_MHz
    SB_MHz = params.SB_MHz
    mult = math.ceil(CPU_MHz/SB_MHz)
    ramTiming = params.RamTiming
    
    tasks = [Task(t.id, t.taskLength, t.isCache, t.useBus, t.isDMA) for t in params.Tasks]

    clock = 0
    mainQueue = copy.deepcopy(tasks)  
    ticks: List[Tick] = []

    while work_remaining():
        tick()
        ticks.append(snapshot(clock))
        clock += 1

    return Cyclogram(ticks=ticks)
    
@app.post("/run/random", response_model=CyclogramRandom)
def run_parameters_random(params: RunRandomParameters):
    print(params)
    global mainQueue, clock, BaseQueue, CPU_MHz, SB_MHz, ramTiming, mult
    CPU_MHz = params.CPU_MHz
    SB_MHz = params.SB_MHz
    mult = math.ceil(CPU_MHz/SB_MHz)
    ramTiming = params.RamTiming
    tasks1, tasks2 = generateTasks(params.TaskTable, params.TaskAmount, params.CacheChance1, params.CacheChance2, params.DMAChance)
    
    clock = 0
    mainQueue = copy.deepcopy(tasks1)  
    ticks: List[Tick] = []

    while work_remaining():
        tick()
        ticks.append(snapshot(clock))
        clock += 1
    tickAmount1 = clock
    
    clock = 0
    mainQueue = copy.deepcopy(tasks2)  
    ticks: List[Tick] = []

    while work_remaining():
        tick()
        ticks.append(snapshot(clock))
        clock += 1
    tickAmount2 = clock
    print(tickAmount1, tickAmount2)
    return CyclogramRandom(ticks=ticks, tickAmount1=tickAmount1, tickAmount2=tickAmount2)

run_all()