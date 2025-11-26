# backend/models/process.py
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class Process:
    pid: int
    arrival_time: int
    burst_time: int
    priority: int = 0
    remaining_time: int = field(init=False)
    wait_time: int = 0
    turnaround_time: int = 0
    completion_time: int = 0
    
    def __post_init__(self):
        self.remaining_time = self.burst_time


# backend/models/execution_result.py
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any

@dataclass
class ExecutionResult:
    execution: Dict[int, Dict[str, Any]]
    metrics: Dict[str, float]
    process_stats: List[Dict[str, Any]]


# backend/algorithms/base_scheduler.py
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from backend.models.process import Process, ExecutionResult

class BaseScheduler(ABC):
    def __init__(self):
        self.execution_timeline = {}
        self.current_time = 0
    
    @abstractmethod
    def schedule(self, processes: List[Process]) -> ExecutionResult:
        pass
    
    def calculate_metrics(self, processes: List[Process]) -> Dict:
        total_wait = sum(p.wait_time for p in processes)
        total_turnaround = sum(p.turnaround_time for p in processes)
        completion_time = max(p.completion_time for p in processes)
        
        return {
            'avg_wait_time': total_wait / len(processes),
            'avg_turnaround_time': total_turnaround / len(processes),
            'total_time': completion_time,
            'cpu_utilization': (completion_time - sum(p.wait_time for p in processes)) / completion_time * 100 if completion_time > 0 else 0,
            'context_switches': self.context_switches
        }
    
    def get_process_stats(self, processes: List[Process]) -> List[Dict]:
        return [
            {
                'PID': p.pid,
                'Arrival': p.arrival_time,
                'Burst': p.burst_time,
                'Wait': p.wait_time,
                'Turnaround': p.turnaround_time,
                'Completion': p.completion_time
            }
            for p in processes
        ]


# backend/algorithms/fcfs.py
from typing import List
from backend.models.process import Process, ExecutionResult
from backend.algorithms.base_scheduler import BaseScheduler

class FCFSScheduler(BaseScheduler):
    def schedule(self, processes: List[Process]) -> ExecutionResult:
        processes = sorted(processes, key=lambda p: p.arrival_time)
        self.context_switches = 0
        self.execution_timeline = {}
        current_time = 0
        
        for process in processes:
            if current_time < process.arrival_time:
                current_time = process.arrival_time
            
            start_time = current_time
            end_time = current_time + process.burst_time
            
            process.wait_time = start_time - process.arrival_time
            process.completion_time = end_time
            process.turnaround_time = process.completion_time - process.arrival_time
            
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))
            
            if self.execution_timeline and list(self.execution_timeline.keys())[-1] != process.pid:
                self.context_switches += 1
            
            current_time = end_time
        
        metrics = self.calculate_metrics(processes)
        process_stats = self.get_process_stats(processes)
        
        return {
            'execution': self.execution_timeline,
            'metrics': metrics,
            'process_stats': process_stats
        }


# backend/algorithms/sjf.py
from typing import List
from backend.models.process import Process, ExecutionResult
from backend.algorithms.base_scheduler import BaseScheduler

class SJFScheduler(BaseScheduler):
    def schedule(self, processes: List[Process]) -> ExecutionResult:
        processes = [p for p in processes]  # Copy
        self.context_switches = 0
        self.execution_timeline = {}
        current_time = 0
        completed = []
        
        while len(completed) < len(processes):
            available = [p for p in processes if p.arrival_time <= current_time and p not in completed]
            
            if not available:
                current_time += 1
                continue
            
            process = min(available, key=lambda p: p.burst_time)
            
            start_time = current_time
            end_time = current_time + process.burst_time
            
            process.wait_time = start_time - process.arrival_time
            process.completion_time = end_time
            process.turnaround_time = process.completion_time - process.arrival_time
            
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))
            
            if self.execution_timeline and list(self.execution_timeline.keys())[-1] != process.pid:
                self.context_switches += 1
            
            completed.append(process)
            current_time = end_time
        
        metrics = self.calculate_metrics(processes)
        process_stats = self.get_process_stats(processes)
        
        return {
            'execution': self.execution_timeline,
            'metrics': metrics,
            'process_stats': process_stats
        }


# backend/algorithms/round_robin.py
from typing import List
from collections import deque
from backend.models.process import Process, ExecutionResult
from backend.algorithms.base_scheduler import BaseScheduler

class RoundRobinScheduler(BaseScheduler):
    def schedule(self, processes: List[Process], quantum: int) -> ExecutionResult:
        processes = [p for p in processes]
        self.context_switches = 0
        self.execution_timeline = {}
        ready_queue = deque()
        current_time = 0
        completed = 0
        
        process_idx = 0
        while completed < len(processes):
            while process_idx < len(processes) and processes[process_idx].arrival_time <= current_time:
                ready_queue.append(processes[process_idx])
                process_idx += 1
            
            if not ready_queue:
                current_time += 1
                continue
            
            process = ready_queue.popleft()
            exec_time = min(quantum, process.remaining_time)
            
            start_time = current_time
            end_time = current_time + exec_time
            
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))
            
            self.context_switches += 1
            process.remaining_time -= exec_time
            current_time = end_time
            
            if process.remaining_time > 0:
                ready_queue.append(process)
            else:
                process.completion_time = current_time
                process.turnaround_time = process.completion_time - process.arrival_time
                process.wait_time = process.turnaround_time - process.burst_time
                completed += 1
        
        metrics = self.calculate_metrics(processes)
        process_stats = self.get_process_stats(processes)
        
        return {
            'execution': self.execution_timeline,
            'metrics': metrics,
            'process_stats': process_stats
        }


# backend/algorithms/priority.py
from typing import List
from backend.models.process import Process, ExecutionResult
from backend.algorithms.base_scheduler import BaseScheduler

class PriorityScheduler(BaseScheduler):
    def schedule(self, processes: List[Process]) -> ExecutionResult:
        processes = [p for p in processes]
        self.context_switches = 0
        self.execution_timeline = {}
        current_time = 0
        completed = []
        
        while len(completed) < len(processes):
            available = [p for p in processes if p.arrival_time <= current_time and p not in completed]
            
            if not available:
                current_time += 1
                continue
            
            process = min(available, key=lambda p: p.priority)
            
            start_time = current_time
            end_time = current_time + process.burst_time
            
            process.wait_time = start_time - process.arrival_time
            process.completion_time = end_time
            process.turnaround_time = process.completion_time - process.arrival_time
            
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))
            
            if self.execution_timeline and list(self.execution_timeline.keys())[-1] != process.pid:
                self.context_switches += 1
            
            completed.append(process)
            current_time = end_time
        
        metrics = self.calculate_metrics(processes)
        process_stats = self.get_process_stats(processes)
        
        return {
            'execution': self.execution_timeline,
            'metrics': metrics,
            'process_stats': process_stats
        }


# backend/simulator.py
from typing import List
from backend.models.process import Process
from backend.algorithms.fcfs import FCFSScheduler
from backend.algorithms.sjf import SJFScheduler
from backend.algorithms.round_robin import RoundRobinScheduler
from backend.algorithms.priority import PriorityScheduler

class CPUScheduler:
    def __init__(self):
        self.fcfs_scheduler = FCFSScheduler()
        self.sjf_scheduler = SJFScheduler()
        self.rr_scheduler = RoundRobinScheduler()
        self.priority_scheduler = PriorityScheduler()
    
    def schedule_fcfs(self, processes: List[Process]):
        return self.fcfs_scheduler.schedule([Process(**vars(p)) for p in processes])
    
    def schedule_sjf(self, processes: List[Process]):
        return self.sjf_scheduler.schedule([Process(**vars(p)) for p in processes])
    
    def schedule_rr(self, processes: List[Process], quantum: int):
        return self.rr_scheduler.schedule([Process(**vars(p)) for p in processes], quantum)
    
    def schedule_priority(self, processes: List[Process]):
        return self.priority_scheduler.schedule([Process(**vars(p)) for p in processes])
