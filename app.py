import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scheduler import CPUScheduler, Process

# ==================== HELPER FUNCTIONS ====================
def _create_gantt_chart(execution_data, algorithm_name):
    """Create interactive Gantt chart"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Plotly
    
    for idx, (process_id, details) in enumerate(execution_data.items()):
        color = colors[idx % len(colors)]
        fig.add_trace(go.Bar(
            y=[f"P{process_id}"] * len(details['intervals']),
            x=[end - start for start, end in details['intervals']],
            base=[start for start, end in details['intervals']],
            name=f"P{process_id}",
            marker=dict(color=color, line=dict(width=1, color='white')),
            hovertemplate="<b>Process %{y}</b><br>Start: %{base}<br>Duration: %{x}<extra></extra>",
            orientation='h'
        ))
    
    fig.update_layout(
        title=f"Gantt Chart - {algorithm_name}",
        xaxis_title="Time (units)",
        yaxis_title="Process",
        barmode='overlay',
        height=300,
        hovermode='closest',
        template='plotly_white',
        showlegend=False,
        margin=dict(l=80, r=20, t=40, b=40)
    )
    
    return fig

def _create_metrics_comparison(results_dict):
    """Create comparison visualization"""
    metrics_data = {
        'Algorithm': [],
        'Avg Wait Time': [],
        'Avg Turnaround Time': [],
        'CPU Utilization': [],
        'Context Switches': []
    }
    
    for algo_name, result in results_dict.items():
        metrics = result['metrics']
        metrics_data['Algorithm'].append(algo_name)
        metrics_data['Avg Wait Time'].append(metrics['avg_wait_time'])
        metrics_data['Avg Turnaround Time'].append(metrics['avg_turnaround_time'])
        metrics_data['CPU Utilization'].append(metrics['cpu_utilization'])
        metrics_data['Context Switches'].append(metrics['context_switches'])
    
    df = pd.DataFrame(metrics_data)
    
    fig = go.Figure(data=[
        go.Bar(name='Avg Wait Time', x=df['Algorithm'], y=df['Avg Wait Time'], marker_color='#1f77b4'),
        go.Bar(name='Avg Turnaround', x=df['Algorithm'], y=df['Avg Turnaround Time'], marker_color='#ff7f0e'),
        go.Bar(name='CPU Utilization %', x=df['Algorithm'], y=df['CPU Utilization'], marker_color='#2ca02c')
    ])
    
    fig.update_layout(
        title="Algorithm Performance Comparison",
        barmode='group',
        height=400,
        template='plotly_white',
        hovermode='x unified',
        margin=dict(l=80, r=20, t=40, b=40)
    )
    
    return fig, df
    
# Page configuration
st.set_page_config(
    page_title="CPU Scheduling Simulator",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main-header {
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    .section-header {
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 0.75rem;
        margin: 2rem 0 1.5rem 0;
        color: #1f77b4;
        font-size: 1.4rem;
        font-weight: 600;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1f77b4 0%, #2ca02c 100%);
        padding: 1.5rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .gantt-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    
    .info-box {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">CPU Scheduling Simulator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Compare and analyze CPU scheduling algorithms with real-time visualization</p>', unsafe_allow_html=True)

# Initialize session state
if 'last_results' not in st.session_state:
    st.session_state.last_results = None

# Create tabs
tab_simulator, tab_comparison, tab_about = st.tabs(["Simulator", "Comparison Analysis", "About"])

# ==================== TAB 1: SIMULATOR ====================
with tab_simulator:
    st.markdown('<div class="section-header">Scheduling Simulation</div>', unsafe_allow_html=True)
    
    col_input, col_display = st.columns([1, 2])
    
    with col_input:
        st.subheader("Process Configuration")
        
        input_method = st.radio("Input Method", ["Manual Entry", "Sample Data"])
        
        processes = []
        
        if input_method == "Manual Entry":
            num_processes = st.number_input("Number of processes", min_value=1, max_value=10, value=3)
            
            for i in range(num_processes):
                with st.expander(f"Process {i+1}", expanded=(i==0)):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        arrival = st.number_input(f"Arrival Time", min_value=0, value=i, key=f"arr_{i}")
                    with col_b:
                        burst = st.number_input(f"Burst Time", min_value=1, value=5, key=f"burst_{i}")
                    with col_c:
                        priority = st.number_input(f"Priority", min_value=1, max_value=10, value=5, key=f"pri_{i}")
                    
                    processes.append(Process(pid=i+1, arrival_time=arrival, burst_time=burst, priority=priority))
        
        else:  # Sample Data
            sample_processes = [
                Process(pid=1, arrival_time=0, burst_time=8, priority=2),
                Process(pid=2, arrival_time=1, burst_time=4, priority=1),
                Process(pid=3, arrival_time=2, burst_time=2, priority=3),
                Process(pid=4, arrival_time=3, burst_time=1, priority=2),
            ]
            processes = sample_processes
            st.success("Sample processes loaded")
        
        st.markdown("---")
        st.subheader("Algorithm Settings")
        quantum = st.slider("Round Robin Quantum", min_value=1, max_value=20, value=4)
        
        st.markdown("---")
        st.subheader("Select Algorithms")
        col_algo1, col_algo2 = st.columns(2)
        with col_algo1:
            run_fcfs = st.checkbox("FCFS", value=True)
            run_rr = st.checkbox("Round Robin", value=True)
        with col_algo2:
            run_sjf = st.checkbox("SJF", value=True)
            run_priority = st.checkbox("Priority", value=True)
    
    with col_display:
        if processes:
            st.subheader("Process Details")
            df_display = pd.DataFrame({
                'PID': [p.pid for p in processes],
                'Arrival Time': [p.arrival_time for p in processes],
                'Burst Time': [p.burst_time for p in processes],
                'Priority': [p.priority for p in processes]
            })
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Run button
    if st.button("Run Simulation", use_container_width=True, type="primary"):
        if not processes:
            st.error("Please configure processes first")
        else:
            with st.spinner("Executing scheduling algorithms..."):
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
                
                st.session_state.last_results = results
                
                # Display results
                st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)
                
                for algo_name, result in results.items():
                    st.markdown(f'<div class="gantt-container">', unsafe_allow_html=True)
                    st.subheader(algo_name)
                    
                    # Gantt chart
                    fig = _create_gantt_chart(result['execution'], algo_name)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Metrics in columns
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    metrics = result['metrics']
                    
                    with metric_col1:
                        st.metric("Avg Wait Time", f"{metrics['avg_wait_time']:.2f}")
                    with metric_col2:
                        st.metric("Avg Turnaround Time", f"{metrics['avg_turnaround_time']:.2f}")
                    with metric_col3:
                        st.metric("CPU Utilization", f"{metrics['cpu_utilization']:.1f}%")
                    with metric_col4:
                        st.metric("Context Switches", metrics['context_switches'])
                    
                    # Process statistics
                    with st.expander("View detailed process statistics"):
                        stats_df = pd.DataFrame(result['process_stats'])
                        st.dataframe(stats_df, use_container_width=True, hide_index=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.success("Simulation completed successfully")

# ==================== TAB 2: COMPARISON ====================
with tab_comparison:
    st.markdown('<div class="section-header">Algorithm Comparison</div>', unsafe_allow_html=True)
    
    if st.session_state.last_results:
        fig, df = _create_metrics_comparison(st.session_state.last_results)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detailed Metrics Table")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Analysis
        st.markdown('<div class="section-header">Analysis</div>', unsafe_allow_html=True)
        
        best_wait = df.loc[df['Avg Wait Time'].idxmin()]
        best_turnaround = df.loc[df['Avg Turnaround Time'].idxmin()]
        best_utilization = df.loc[df['CPU Utilization'].idxmax()]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"Best Wait Time: {best_wait['Algorithm']}\n({best_wait['Avg Wait Time']:.2f})")
        with col2:
            st.info(f"Best Turnaround: {best_turnaround['Algorithm']}\n({best_turnaround['Avg Turnaround Time']:.2f})")
        with col3:
            st.info(f"Best Utilization: {best_utilization['Algorithm']}\n({best_utilization['CPU Utilization']:.1f}%)")
    else:
        st.markdown('<div class="info-box">Run a simulation first to see comparison analysis</div>', unsafe_allow_html=True)

# ==================== TAB 3: ABOUT ====================
with tab_about:
    st.markdown('<div class="section-header">About This Project</div>', unsafe_allow_html=True)
    
    st.write("""
    ## CPU Scheduling Simulator
    
    This application demonstrates and compares four fundamental CPU scheduling algorithms 
    used in modern operating systems.
    
    ### Algorithms
    
    **FCFS (First Come First Served)**
    - Non-preemptive scheduling
    - Processes execute in the order of arrival
    - Simple but can suffer from convoy effect
    - Best for batch systems
    
    **SJF (Shortest Job First)**
    - Non-preemptive scheduling
    - Selects process with shortest burst time
    - Minimizes average waiting time
    - May cause starvation of longer jobs
    
    **Round Robin**
    - Preemptive scheduling
    - Each process gets a time quantum
    - Fair distribution of CPU time
    - Ideal for time-sharing systems
    
    **Priority Scheduling**
    - Non-preemptive scheduling
    - Selects process with highest priority
    - Supports real-time requirements
    - Risk of starvation for low-priority processes
    
    ### Metrics Explained
    
    - **Average Wait Time**: Average time processes spend waiting in the ready queue
    - **Average Turnaround Time**: Average total time from arrival to completion
    - **CPU Utilization**: Percentage of time CPU is actively executing processes
    - **Context Switches**: Number of times CPU switches between processes
    
    ### How to Use
    
    1. Configure processes with arrival time, burst time, and priority
    2. Set Round Robin quantum (time slice)
    3. Select which algorithms to compare
    4. Click "Run Simulation"
    5. View results and analyze performance
    
    ### Technology Stack
    - Python
    - Streamlit (Frontend)
    - Plotly (Visualization)
    - Pandas (Data Processing)
    """)
