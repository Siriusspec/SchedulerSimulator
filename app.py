import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scheduler import CPUScheduler
from backend.models.process import Process

# Page configuration
st.set_page_config(
    page_title="CPU Scheduling Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .gantt-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .section-header {
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def create_gantt_chart(execution_data, algorithm_name):
    """Create interactive Gantt chart using Plotly"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Plotly
    
    for idx, (process_id, details) in enumerate(execution_data.items()):
        color = colors[idx % len(colors)]
        fig.add_trace(go.Bar(
            y=[process_id] * len(details['intervals']),
            x=[end - start for start, end in details['intervals']],
            base=[start for start, end in details['intervals']],
            name=f"P{process_id}",
            marker=dict(color=color),
            hovertemplate=f"<b>Process {process_id}</b><br>Start: %{{base}}<br>Duration: %{{x}}<extra></extra>",
            orientation='h'
        ))
    
    fig.update_layout(
        title=f"Gantt Chart - {algorithm_name}",
        xaxis_title="Time",
        yaxis_title="Process",
        barmode='overlay',
        height=300,
        hovermode='closest',
        template='plotly_white',
        showlegend=True
    )
    
    return fig

def create_metrics_comparison(results_dict):
    """Create comparison chart for metrics"""
    metrics_data = {
        'Algorithm': [],
        'Avg Wait Time': [],
        'Avg Turnaround': [],
        'CPU Utilization': []
    }
    
    for algo_name, result in results_dict.items():
        metrics_data['Algorithm'].append(algo_name)
        metrics_data['Avg Wait Time'].append(result['metrics']['avg_wait_time'])
        metrics_data['Avg Turnaround'].append(result['metrics']['avg_turnaround_time'])
        metrics_data['CPU Utilization'].append(result['metrics']['cpu_utilization'])
    
    df = pd.DataFrame(metrics_data)
    
    fig = go.Figure(data=[
        go.Bar(name='Avg Wait Time', x=df['Algorithm'], y=df['Avg Wait Time']),
        go.Bar(name='Avg Turnaround', x=df['Algorithm'], y=df['Avg Turnaround']),
        go.Bar(name='CPU Utilization %', x=df['Algorithm'], y=df['CPU Utilization'])
    ])
    
    fig.update_layout(
        title="Algorithm Comparison",
        barmode='group',
        height=400,
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig, df

# Sidebar for input
st.sidebar.markdown("# ⚙️ Scheduler Configuration")

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Simulator", "📊 Comparison", "📚 About", "🧪 Presets"])

with tab1:
    st.markdown('<div class="section-header"><h2>CPU Scheduling Simulator</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📋 Process Input")
        
        input_method = st.radio("Choose input method:", ["Manual Entry", "JSON Upload", "Sample Data"])
        
        processes = []
        
        if input_method == "Manual Entry":
            num_processes = st.number_input("Number of processes:", min_value=1, max_value=10, value=3)
            
            for i in range(num_processes):
                st.write(f"**Process {i+1}**")
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    arrival = st.number_input(f"Arrival (P{i+1}):", min_value=0, key=f"arr_{i}")
                with col_b:
                    burst = st.number_input(f"Burst (P{i+1}):", min_value=1, key=f"burst_{i}")
                with col_c:
                    priority = st.number_input(f"Priority (P{i+1}):", min_value=0, max_value=10, value=5, key=f"pri_{i}")
                
                processes.append(Process(pid=i+1, arrival_time=arrival, burst_time=burst, priority=priority))
        
        elif input_method == "Sample Data":
            sample_processes = [
                Process(pid=1, arrival_time=0, burst_time=8, priority=2),
                Process(pid=2, arrival_time=1, burst_time=4, priority=1),
                Process(pid=3, arrival_time=2, burst_time=2, priority=3),
                Process(pid=4, arrival_time=3, burst_time=1, priority=2),
            ]
            processes = sample_processes
            st.success("✓ Sample processes loaded")
        
        quantum = st.number_input("Round Robin Quantum:", min_value=1, max_value=20, value=4)
    
    with col2:
        if processes:
            st.subheader("📊 Selected Processes")
            df_display = pd.DataFrame({
                'PID': [p.pid for p in processes],
                'Arrival Time': [p.arrival_time for p in processes],
                'Burst Time': [p.burst_time for p in processes],
                'Priority': [p.priority for p in processes]
            })
            st.dataframe(df_display, use_container_width=True)
    
    # Algorithm selection
    st.markdown('<div class="section-header"><h3>Select Algorithms</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_fcfs = st.checkbox("FCFS", value=True)
    with col2:
        run_sjf = st.checkbox("SJF", value=True)
    with col3:
        run_rr = st.checkbox("Round Robin", value=True)
    with col4:
        run_priority = st.checkbox("Priority", value=True)
    
    if st.button("▶️ Run Simulation", use_container_width=True, type="primary"):
        if not processes:
            st.error("❌ Please add processes first")
        else:
            with st.spinner("Running simulations..."):
                scheduler = CPUScheduler()
                results = {}
                
                if run_fcfs:
                    results['FCFS'] = scheduler.schedule_fcfs(processes)
                if run_sjf:
                    results['SJF'] = scheduler.schedule_sjf(processes)
                if run_rr:
                    results['Round Robin'] = scheduler.schedule_rr(processes, quantum)
                if run_priority:
                    results['Priority'] = scheduler.schedule_priority(processes)
                
                # Display results
                for algo_name, result in results.items():
                    st.markdown(f'<div class="gantt-container">', unsafe_allow_html=True)
                    st.subheader(f"📊 {algo_name}")
                    
                    # Gantt chart
                    fig = create_gantt_chart(result['execution'], algo_name)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    metrics = result['metrics']
                    
                    with col1:
                        st.metric("Avg Wait Time", f"{metrics['avg_wait_time']:.2f}")
                    with col2:
                        st.metric("Avg Turnaround", f"{metrics['avg_turnaround_time']:.2f}")
                    with col3:
                        st.metric("CPU Utilization", f"{metrics['cpu_utilization']:.1f}%")
                    with col4:
                        st.metric("Context Switches", metrics['context_switches'])
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Store results in session state for comparison
                st.session_state.last_results = results
                st.success("✓ Simulation complete!")

with tab2:
    st.markdown('<div class="section-header"><h2>Algorithm Comparison</h2></div>', unsafe_allow_html=True)
    
    if 'last_results' in st.session_state and st.session_state.last_results:
        fig, df = create_metrics_comparison(st.session_state.last_results)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Detailed Metrics")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("💡 Run a simulation first to see comparisons")

with tab3:
    st.markdown('<div class="section-header"><h2>About This Project</h2></div>', unsafe_allow_html=True)
    
    st.write("""
    ### CPU Scheduling Simulator
    
    This project demonstrates various CPU scheduling algorithms used in operating systems.
    
    **Algorithms Implemented:**
    - **FCFS** (First Come First Served): Non-preemptive, simple FIFO queue
    - **SJF** (Shortest Job First): Non-preemptive, chooses process with shortest burst time
    - **Round Robin**: Preemptive, time quantum-based scheduling
    - **Priority Scheduling**: Non-preemptive, based on process priority
    
    **Metrics Calculated:**
    - Waiting Time: Time spent in ready queue
    - Turnaround Time: Total time from arrival to completion
    - CPU Utilization: Percentage of time CPU is active
    - Context Switches: Number of times CPU switches between processes
    
    **Tech Stack:** Python, Streamlit, Plotly
    """)

with tab4:
    st.markdown('<div class="section-header"><h2>Preset Scenarios</h2></div>', unsafe_allow_html=True)
    
    st.write("Quick-load test scenarios (copy to Manual Entry):")
    
    scenarios = {
        "Scenario 1: Equal Burst Times": [
            {"PID": 1, "Arrival": 0, "Burst": 5, "Priority": 1},
            {"PID": 2, "Arrival": 0, "Burst": 5, "Priority": 1},
            {"PID": 3, "Arrival": 0, "Burst": 5, "Priority": 1},
        ],
        "Scenario 2: Varying Load": [
            {"PID": 1, "Arrival": 0, "Burst": 10, "Priority": 2},
            {"PID": 2, "Arrival": 1, "Burst": 2, "Priority": 1},
            {"PID": 3, "Arrival": 3, "Burst": 8, "Priority": 3},
            {"PID": 4, "Arrival": 5, "Burst": 4, "Priority": 1},
        ]
    }
    
    for name, data in scenarios.items():
        with st.expander(name):
            st.dataframe(pd.DataFrame(data))
