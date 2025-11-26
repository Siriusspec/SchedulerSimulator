# CPU Scheduling Simulator

A comprehensive **web-based application** for visualizing and comparing CPU scheduling algorithms used in operating systems.  
Built with **Python**, **Streamlit**, and **Plotly** for interactive data visualization.

---

## Features
- **Interactive Visualization**: Real-time Gantt charts showing process execution timelines  
- **Multiple Algorithms**: Compare FCFS, SJF, Round Robin, and Priority scheduling  
- **Flexible Input**: Configure processes manually or use pre-loaded sample data  
- **Performance Metrics**: Detailed analysis including wait time, turnaround time, CPU utilization, and context switches  
- **Comparison Analysis**: Side-by-side performance comparison of different algorithms  
- **Responsive UI**: Modern, professional interface with intuitive controls  
- **Export Ready**: Statistical data available in tabular format  

---

## Algorithms Implemented

### 1. FCFS (First Come First Served)
- **Type**: Non-preemptive  
- **Selection Criteria**: Arrival time  
- **Best For**: Batch processing systems  
- **Characteristics**: Simple implementation, may suffer from convoy effect  

### 2. SJF (Shortest Job First)
- **Type**: Non-preemptive  
- **Selection Criteria**: Shortest burst time  
- **Best For**: Minimizing average waiting time  
- **Characteristics**: Optimal for average wait time, risk of starvation  

### 3. Round Robin
- **Type**: Preemptive  
- **Selection Criteria**: Time quantum rotation  
- **Best For**: Time-sharing systems  
- **Characteristics**: Fair CPU distribution, configurable quantum  

### 4. Priority Scheduling
- **Type**: Non-preemptive  
- **Selection Criteria**: Process priority (lower number = higher priority)  
- **Best For**: Real-time systems  
- **Characteristics**: Supports urgency levels, risk of starvation for low-priority processes  

---
