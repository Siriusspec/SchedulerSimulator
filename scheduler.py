from dataclasses import dataclass, field
from typing import List, Dict, Any
from collections import deque
import copy

# ==================== DATA MODELS ====================
@dataclass
class Process:
    """Represents a process with scheduling attributes"""
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

    def __deepcopy__(self, memo):
        """Enable deep copying of Process objects"""
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, copy.deepcopy(v, memo))
        return result


# ==================== BASE SCHEDULER ====================
class BaseScheduler:
    """Base class for CPU scheduling algorithms"""

    def __init__(self):
        self.execution_timeline = {}
        self.context_switches = 0

    def calculate_metrics(self, processes: List[Process]) -> Dict[str, float]:
        """Calculate scheduling metrics"""
        if not processes:
            return {}

        total_wait = sum(p.wait_time for p in processes)
        total_turnaround = sum(p.turnaround_time for p in processes)

        avg_wait = total_wait / len(processes)
        avg_turnaround = total_turnaround / len(processes)

        # CPU utilization = total busy time / total elapsed time
        busy_time = sum(p.burst_time for p in processes)
        earliest_arrival = min(p.arrival_time for p in processes)
        last_completion = max(p.completion_time for p in processes)
        total_time = last_completion - earliest_arrival if last_completion > earliest_arrival else 0
        cpu_util = (busy_time / total_time) * 100 if total_time > 0 else 0

        return {
            'avg_wait_time': avg_wait,
            'avg_turnaround_time': avg_turnaround,
            'total_time': total_time,
            'cpu_utilization': cpu_util,
            'context_switches': self.context_switches
        }

    def get_process_stats(self, processes: List[Process]) -> List[Dict[str, Any]]:
        """Get detailed statistics for each process"""
        return [
            {
                'PID': p.pid,
                'Arrival': p.arrival_time,
                'Burst': p.burst_time,
                'Wait Time': p.wait_time,
                'Turnaround': p.turnaround_time,
                'Completion': p.completion_time
            }
            for p in processes
        ]


# ==================== FCFS SCHEDULER ====================
class FCFSScheduler(BaseScheduler):
    """First Come First Served Scheduling"""

    def schedule(self, processes: List[Process]) -> Dict[str, Any]:
        """Execute FCFS scheduling"""
        # Work on a deep copy and sort by arrival to avoid mutating caller objects
        processes = sorted(copy.deepcopy(processes), key=lambda p: p.arrival_time)
        self.context_switches = 0
        self.execution_timeline = {}
        current_time = 0
        last_executed_pid = None
        last_end_time = None

        for process in processes:
            # If CPU is idle, advance time to process arrival
            if current_time < process.arrival_time:
                current_time = process.arrival_time

            start_time = current_time
            end_time = current_time + process.burst_time

            # Calculate metrics
            process.wait_time = start_time - process.arrival_time
            process.completion_time = end_time
            process.turnaround_time = process.completion_time - process.arrival_time

            # Track execution
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))

            # Count context switches: only if there was a different last executed process and CPU did not stay idle returning to same
            if last_executed_pid is not None and last_executed_pid != process.pid:
                # If CPU was idle (start_time > last_end_time) this still counts as a "switch" in UI terms,
                # but some definitions don't count idle -> first process as a context switch. Keep count consistent.
                self.context_switches += 1

            last_executed_pid = process.pid
            last_end_time = end_time
            current_time = end_time

        metrics = self.calculate_metrics(processes)
        process_stats = self.get_process_stats(processes)

        return {
            'execution': self.execution_timeline,
            'metrics': metrics,
            'process_stats': process_stats
        }


# ==================== SJF SCHEDULER ====================
class SJFScheduler(BaseScheduler):
    """Shortest Job First Scheduling (non-preemptive)"""

    def schedule(self, processes: List[Process]) -> Dict[str, Any]:
        """Execute SJF scheduling"""
        processes = copy.deepcopy(processes)
        processes = sorted(processes, key=lambda p: p.arrival_time)  # sort by arrival for determinism
        self.context_switches = 0
        self.execution_timeline = {}
        current_time = 0
        completed = []

        while len(completed) < len(processes):
            # Find available processes
            available = [p for p in processes if p.arrival_time <= current_time and p not in completed]

            if not available:
                # CPU idle, advance to next arrival
                next_arrival = min(p.arrival_time for p in processes if p not in completed)
                current_time = next_arrival
                continue

            # Select process with shortest burst time
            process = min(available, key=lambda p: p.burst_time)

            start_time = current_time
            end_time = current_time + process.burst_time

            # Calculate metrics
            process.wait_time = start_time - process.arrival_time
            process.completion_time = end_time
            process.turnaround_time = process.completion_time - process.arrival_time

            # Track execution
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))

            # Count context switches
            if len(self.execution_timeline) > 1 and list(self.execution_timeline.keys())[-2] != process.pid:
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


# ==================== ROUND ROBIN SCHEDULER ====================
class RoundRobinScheduler(BaseScheduler):
    """Round Robin Scheduling with time quantum"""

    def schedule(self, processes: List[Process], quantum: int) -> Dict[str, Any]:
        """Execute Round Robin scheduling"""
        # Work on sorted deep copy to ensure arrival order and avoid side-effects
        processes = sorted(copy.deepcopy(processes), key=lambda p: p.arrival_time)
        self.context_switches = 0
        self.execution_timeline = {}
        ready_queue = deque()
        current_time = 0
        completed = 0
        process_idx = 0
        last_process = None
        last_end_time = None

        while completed < len(processes):
            # Add newly arrived processes to queue
            while process_idx < len(processes) and processes[process_idx].arrival_time <= current_time:
                ready_queue.append(processes[process_idx])
                process_idx += 1

            if not ready_queue:
                # CPU idle, advance to next arrival
                if process_idx < len(processes):
                    current_time = processes[process_idx].arrival_time
                continue

            # Dequeue process
            process = ready_queue.popleft()

            # Execute for time quantum or remaining time
            exec_time = min(quantum, process.remaining_time)
            start_time = current_time
            end_time = current_time + exec_time

            # Track context switch: only count if previous execution existed and pid differs and CPU wasn't idle but returned to same immediately
            if last_process is not None and last_process != process.pid:
                # If CPU was idle between last_end_time and start_time, we still consider it a switch in most UIs.
                self.context_switches += 1

            # Track execution segments
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))

            # Update process and time
            process.remaining_time -= exec_time
            current_time = end_time

            # Enqueue newly arrived during execution
            while process_idx < len(processes) and processes[process_idx].arrival_time <= current_time:
                ready_queue.append(processes[process_idx])
                process_idx += 1

            if process.remaining_time > 0:
                # Process not finished, re-queue
                ready_queue.append(process)
            else:
                # Process completed
                process.completion_time = current_time
                process.turnaround_time = process.completion_time - process.arrival_time
                process.wait_time = process.turnaround_time - process.burst_time
                completed += 1

            last_process = process.pid
            last_end_time = end_time

        metrics = self.calculate_metrics(processes)
        process_stats = self.get_process_stats(processes)

        return {
            'execution': self.execution_timeline,
            'metrics': metrics,
            'process_stats': process_stats
        }


# ==================== PRIORITY SCHEDULER ====================
class PriorityScheduler(BaseScheduler):
    """Priority Based Scheduling (Non-preemptive)"""

    def schedule(self, processes: List[Process]) -> Dict[str, Any]:
        """Execute Priority scheduling"""
        processes = copy.deepcopy(processes)
        processes = sorted(processes, key=lambda p: p.arrival_time)
        self.context_switches = 0
        self.execution_timeline = {}
        current_time = 0
        completed = []

        while len(completed) < len(processes):
            # Find available processes
            available = [p for p in processes if p.arrival_time <= current_time and p not in completed]

            if not available:
                # CPU idle, advance to next arrival
                current_time = min(p.arrival_time for p in processes if p not in completed)
                continue

            # Select process with highest priority (lowest number)
            process = min(available, key=lambda p: p.priority)

            start_time = current_time
            end_time = current_time + process.burst_time

            # Calculate metrics
            process.wait_time = start_time - process.arrival_time
            process.completion_time = end_time
            process.turnaround_time = process.completion_time - process.arrival_time

            # Track execution
            if process.pid not in self.execution_timeline:
                self.execution_timeline[process.pid] = {'intervals': []}
            self.execution_timeline[process.pid]['intervals'].append((start_time, end_time))

            # Count context switches
            if len(self.execution_timeline) > 1 and list(self.execution_timeline.keys())[-2] != process.pid:
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


# ==================== CPU SCHEDULER COORDINATOR ====================
class CPUScheduler:
    """Main scheduler that coordinates all algorithms"""

    def __init__(self):
        self.fcfs_scheduler = FCFSScheduler()
        self.sjf_scheduler = SJFScheduler()
        self.rr_scheduler = RoundRobinScheduler()
        self.priority_scheduler = PriorityScheduler()

    def schedule_fcfs(self, processes: List[Process]) -> Dict[str, Any]:
        """Run FCFS scheduling"""
        return self.fcfs_scheduler.schedule(processes)

    def schedule_sjf(self, processes: List[Process]) -> Dict[str, Any]:
        """Run SJF scheduling"""
        return self.sjf_scheduler.schedule(processes)

    def schedule_rr(self, processes: List[Process], quantum: int) -> Dict[str, Any]:
        """Run Round Robin scheduling"""
        return self.rr_scheduler.schedule(processes, quantum)

    def schedule_priority(self, processes: List[Process]) -> Dict[str, Any]:
        """Run Priority scheduling"""
        return self.priority_scheduler.schedule(processes)
