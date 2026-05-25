import streamlit as st
import time
import os
import copy
from solver import (
    solve_sudoku_astar_generator,
    PRESETS,
    is_valid_board,
    generate_random_puzzle_board,
    count_empty_cells
)

# Page Configuration
st.set_page_config(
    page_title="Intelligent Sudoku Solver Agent Using A*",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Read and Inject style.css
CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("Custom CSS file not found. Falling back to default Streamlit styles.")

# Helper to sync input cells back to session state board
def sync_input_to_board():
    for r in range(9):
        for c in range(9):
            key = f"cell_input_{r}_{c}"
            if key in st.session_state:
                val_str = st.session_state[key].strip()
                if val_str.isdigit() and 1 <= int(val_str) <= 9:
                    st.session_state.board[r][c] = int(val_str)
                else:
                    st.session_state.board[r][c] = 0

# Helper to force-sync session state widget inputs from the actual board representation
# This overrides Streamlit's internal widget caching bug!
def update_inputs_from_board():
    for r in range(9):
        for c in range(9):
            key = f"cell_input_{r}_{c}"
            val = st.session_state.board[r][c]
            st.session_state[key] = str(val) if val != 0 else ""

# Callbacks for reactive UI updates when selectbox choices change
def on_preset_change():
    preset_name = st.session_state.preset_select
    st.session_state.board = copy.deepcopy(PRESETS[preset_name])
    st.session_state.original_board = copy.deepcopy(PRESETS[preset_name])
    st.session_state.solved_board = None
    st.session_state.solving_status = "idle"
    st.session_state.explored_states = 0
    st.session_state.solving_time = 0.0
    st.session_state.active_cell = None
    st.session_state.is_visualizing = False
    update_inputs_from_board()

def on_difficulty_change():
    diff_name = st.session_state.difficulty_select
    rand_board = generate_random_puzzle_board(diff_name)
    st.session_state.board = copy.deepcopy(rand_board)
    st.session_state.original_board = copy.deepcopy(rand_board)
    st.session_state.solved_board = None
    st.session_state.solving_status = "idle"
    st.session_state.explored_states = 0
    st.session_state.solving_time = 0.0
    st.session_state.active_cell = None
    st.session_state.is_visualizing = False
    update_inputs_from_board()

# Initialize Session State
if "board" not in st.session_state:
    st.session_state.board = copy.deepcopy(PRESETS["Easy"])
if "original_board" not in st.session_state:
    st.session_state.original_board = copy.deepcopy(PRESETS["Easy"])
if "solved_board" not in st.session_state:
    st.session_state.solved_board = None
if "explored_states" not in st.session_state:
    st.session_state.explored_states = 0
if "solving_time" not in st.session_state:
    st.session_state.solving_time = 0.0
if "solving_status" not in st.session_state:
    st.session_state.solving_status = "idle" # idle, running, solved, unsolvable, invalid
if "active_cell" not in st.session_state:
    st.session_state.active_cell = None
if "is_visualizing" not in st.session_state:
    st.session_state.is_visualizing = False

# Sidebar Controls
with st.sidebar:
    with st.container(border=True):
        st.markdown("## ⚙️ Control Dashboard")
        
        # Preset puzzle selector with instant callback
        preset_opt = st.selectbox(
            "Select Preset Puzzle",
            options=list(PRESETS.keys()),
            index=0,
            key="preset_select",
            on_change=on_preset_change,
            help="Choose a pre-configured puzzle to test the AI solver."
        )
        
        # Load preset logic (renamed to Reset to clarify it is loaded automatically)
        if st.button("🔄 Reset Current Grid", use_container_width=True):
            st.session_state.board = copy.deepcopy(PRESETS[preset_opt])
            st.session_state.original_board = copy.deepcopy(PRESETS[preset_opt])
            st.session_state.solved_board = None
            st.session_state.solving_status = "idle"
            st.session_state.explored_states = 0
            st.session_state.solving_time = 0.0
            st.session_state.active_cell = None
            st.session_state.is_visualizing = False
            update_inputs_from_board()
            st.rerun()
            
        st.markdown("---")
        
        # Random generator selector with instant callback
        diff_opt = st.selectbox(
            "Generator Difficulty", 
            options=["Easy", "Medium", "Hard"],
            index=1, # Default to Medium
            key="difficulty_select",
            on_change=on_difficulty_change
        )
        if st.button("🎲 Generate Another Random", use_container_width=True):
            rand_board = generate_random_puzzle_board(diff_opt)
            st.session_state.board = copy.deepcopy(rand_board)
            st.session_state.original_board = copy.deepcopy(rand_board)
            st.session_state.solved_board = None
            st.session_state.solving_status = "idle"
            st.session_state.explored_states = 0
            st.session_state.solving_time = 0.0
            st.session_state.active_cell = None
            st.session_state.is_visualizing = False
            update_inputs_from_board()
            st.rerun()
            
        st.markdown("---")
        
        # Visualization Delay slider
        st.markdown("##### ⏱️ Visualization Speed")
        delay = st.slider(
            "Delay between steps (seconds)",
            min_value=0.0,
            max_value=0.5,
            value=0.05,
            step=0.01,
            help="Slow down to see the A* search explore states step-by-step."
        )
        
        st.markdown("---")
        
        # Reset/Clear board button
        if st.button("🧹 Clear Grid", use_container_width=True):
            st.session_state.board = copy.deepcopy(PRESETS["Empty Grid"])
            st.session_state.original_board = copy.deepcopy(PRESETS["Empty Grid"])
            st.session_state.solved_board = None
            st.session_state.solving_status = "idle"
            st.session_state.explored_states = 0
            st.session_state.solving_time = 0.0
            st.session_state.active_cell = None
            st.session_state.is_visualizing = False
            update_inputs_from_board()
            st.rerun()
            
    # Short about section in sidebar
    with st.container(border=True):
        st.markdown("### 🤖 About the Agent")
        st.markdown(
            """
            This AI agent solves Sudoku using the **A* Search Algorithm**, which is a pathfinding and graph traversal algorithm. 
            
            By modeling Sudoku as a **Constraint Satisfaction Problem (CSP)**, the agent uses A* alongside the **Minimum Remaining Values (MRV)** heuristic to find the solution.
            """
        )

# Main Application Layout
st.markdown('<h1 style="text-align: center;"><span class="gradient-text">🧩 Intelligent Sudoku Solver Agent</span><br><small style="font-size: 16px; font-weight: 400; color: #64748b;">Powered by A* Search & Constraint Propagation</small></h1>', unsafe_allow_html=True)

# Layout division
main_col, side_col = st.columns([1.1, 0.9], gap="large")

# Render HTML Grid representation function
def draw_html_grid(board, active_cell=None, original_board=None):
    html = '<div class="sudoku-container"><table class="sudoku-visualizer-table">'
    for r in range(9):
        html += '<tr>'
        for c in range(9):
            classes = ["sudoku-cell"]
            # thick borders for 3x3 boundaries
            if c in [2, 5]:
                classes.append("border-right-thick")
            if r in [2, 5]:
                classes.append("border-bottom-thick")
                
            val = board[r][c]
            val_str = str(val) if val != 0 else ""
            
            if active_cell and active_cell == (r, c):
                classes.append("cell-active")
                if val == 0:
                    val_str = "?" # Indicator for evaluation
            elif val == 0:
                classes.append("cell-empty")
                val_str = "&nbsp;"
            elif original_board and original_board[r][c] != 0:
                classes.append("cell-initial")
            else:
                classes.append("cell-solved")
                
            class_attr = " ".join(classes)
            html += f'<td class="{class_attr}">{val_str}</td>'
        html += '</tr>'
    html += '</table></div>'
    return html

# ----------------- LEFT COLUMN: Board & Solve buttons -----------------
with main_col:
    with st.container(border=True):
        st.markdown("### 🧩 Sudoku Board")
        
        # If currently solving/visualizing or solved, we show the read-only HTML visualizer.
        # Otherwise, we show interactive inputs for manual editing.
        if st.session_state.is_visualizing or st.session_state.solving_status == "solved" or st.session_state.solving_status == "unsolvable":
            # Visualization / Solved Read-only mode
            grid_html = draw_html_grid(
                st.session_state.board,
                active_cell=st.session_state.active_cell,
                original_board=st.session_state.original_board
            )
            st.markdown(grid_html, unsafe_allow_html=True)
        else:
            # Edit / Manual Input mode
            st.caption("✍️ Click any cell to manually edit numbers (1-9). Leave blank or delete to clear cells.")
            
            # We render 9 columns of input text boxes
            grid_cols = st.columns(9)
            for c in range(9):
                with grid_cols[c]:
                    for r in range(9):
                        val = st.session_state.board[r][c]
                        val_str = str(val) if val != 0 else ""
                        
                        # Compute borders logic to apply styling classes if desired (handled in style.css input)
                        st.text_input(
                            label=f"r{r}c{c}",
                            value=val_str,
                            key=f"cell_input_{r}_{c}",
                            label_visibility="collapsed",
                            on_change=sync_input_to_board
                        )
                        
        # Sync board from inputs before running
        sync_input_to_board()
        
        # Quick info about empty cells remaining
        empty_cnt = count_empty_cells(st.session_state.board)
        st.markdown(f'<span class="metric-badge">Empty Cells Remaining: {empty_cnt} / 81</span>', unsafe_allow_html=True)
        
        st.markdown("#### ⚡ Solver Controls")
        
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            visual_btn = st.button(
                "🎬 Solve with Visualization",
                key="visual_solve_button",
                use_container_width=True,
                disabled=st.session_state.is_visualizing
            )
        with btn_col2:
            instant_btn = st.button(
                "⚡ Instant Solve",
                key="solve_button",
                use_container_width=True,
                disabled=st.session_state.is_visualizing
            )
    
    # ------------------ SOLVER EXECUTION ------------------
    if visual_btn or instant_btn:
        # Check initial validation
        if not is_valid_board(st.session_state.board):
            st.session_state.solving_status = "invalid"
            st.error("⚠️ Invalid Initial Sudoku Grid! Please check for duplicate numbers in any row, column, or 3x3 block.")
        else:
            # Prepare state
            st.session_state.original_board = copy.deepcopy(st.session_state.board)
            st.session_state.solved_board = None
            st.session_state.is_visualizing = True
            st.session_state.solving_status = "running"
            
            # Create a clean board container to update live
            board_placeholder = st.empty()
            metrics_placeholder = st.empty()
            
            start_time = time.time()
            
            if visual_btn:
                # RUN VISUAL SOLVE
                generator = solve_sudoku_astar_generator(st.session_state.board)
                last_update = time.time()
                
                for curr_board, active_cell, explored_count, status in generator:
                    if curr_board is not None:
                        st.session_state.board = curr_board
                    st.session_state.active_cell = active_cell
                    st.session_state.explored_states = explored_count
                    st.session_state.solving_time = time.time() - start_time
                    st.session_state.solving_status = status
                    
                    # Update board grid visual
                    if curr_board is not None:
                        board_placeholder.markdown(
                            draw_html_grid(curr_board, active_cell, st.session_state.original_board),
                            unsafe_allow_html=True
                        )
                    
                    # Throttled / sleeping for animation speed
                    if delay > 0:
                        time.sleep(delay)
                    elif time.time() - last_update > 0.05: # Throttle rendering if delay is 0 for smooth UI
                        time.sleep(0.001)
                        last_update = time.time()
                        
                st.session_state.is_visualizing = False
                st.session_state.active_cell = None
                st.rerun()
                
            else:
                # RUN INSTANT SOLVE
                generator = solve_sudoku_astar_generator(st.session_state.board)
                final_board = None
                final_status = "unsolvable"
                final_explored = 0
                
                for curr_board, active_cell, explored_count, status in generator:
                    final_board = curr_board
                    final_status = status
                    final_explored = explored_count
                    
                st.session_state.board = final_board if final_board else st.session_state.board
                st.session_state.solving_status = final_status
                st.session_state.explored_states = final_explored
                st.session_state.solving_time = time.time() - start_time
                st.session_state.is_visualizing = False
                st.session_state.active_cell = None
                st.rerun()
                
    # Display Solving Outcomes
    if st.session_state.solving_status == "solved":
        st.markdown(
            f'<div class="solved-alert">🎉 Success! Sudoku solved perfectly using A* algorithm in {st.session_state.solving_time:.4f} seconds!</div>',
            unsafe_allow_html=True
        )
    elif st.session_state.solving_status == "unsolvable":
        st.error("❌ Unsolvable Sudoku! No valid configuration satisfies the constraints for this board.")
    elif st.session_state.solving_status == "limit_reached":
        st.warning("⚠️ Limit Reached! The search space exceeded the safe threshold without finding a solution.")

# ----------------- RIGHT COLUMN: About & Explanation -----------------
with side_col:
    # 1. Performance Metrics Card
    with st.container(border=True):
        st.markdown("### 📊 Performance & Search Metrics")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric(
                label="⏱️ Execution Time",
                value=f"{st.session_state.solving_time:.4f} s" if st.session_state.solving_time > 0 else "0.0000 s"
            )
            st.metric(
                label="🔬 Explored States",
                value=f"{st.session_state.explored_states}"
            )
        with col_m2:
            # Solved states per second
            if st.session_state.solving_time > 0:
                states_per_sec = int(st.session_state.explored_states / st.session_state.solving_time)
            else:
                states_per_sec = 0
            st.metric(
                label="⚡ Search Velocity",
                value=f"{states_per_sec:,} st/s" if states_per_sec > 0 else "0 st/s"
            )
            # Search Status
            status_badges = {
                "idle": "⚪ Idle (Awaiting Input)",
                "running": "🔵 Solving in Progress...",
                "solved": "🟢 Solved Successfully",
                "unsolvable": "🔴 No Solution Exists",
                "invalid": "🟡 Invalid Initial Board",
                "limit_reached": "🟠 Max States Reached"
            }
            st.metric(
                label="📡 Agent Status",
                value=status_badges.get(st.session_state.solving_status, "Idle")
            )
 
    # 2. Algorithm Explanation Card
    with st.container(border=True):
        st.markdown("### 🧠 AI Agent & Algorithm Walkthrough")
        
        st.markdown(
            """
            The solver models the Sudoku grid search space and navigates it using the **A* Algorithm**.
            
            #### 1. Mathematical Formulation
            The A* algorithm evaluates nodes using the cost function:
            $$f(n) = g(n) + h(n)$$
            
            *   **$g(n)$ (Path Cost)**: The number of moves (digits filled) made by the solver from the initial starting configuration.
            *   **$h(n)$ (Heuristic Cost)**: The number of remaining empty cells on the grid.
            
            $$\\text{Note: For any branch, } g(n) + h(n) = \\text{constant } (81 - K)$$
            
            #### 2. Advanced Constraint Optimization Heuristics
            To break ties and dramatically prune the search tree, this agent incorporates **Constraint Satisfaction** heuristics:
            
            *   **Minimum Remaining Values (MRV)**: Instead of filling cells sequentially (row by row), the agent searches the entire board to find the empty cell with the **absolute fewest legal candidate numbers** remaining. 
            *   **Fail-Fast Pruning**: If the agent detects an empty cell that has **zero valid options**, it flags the branch as a dead-end and backtracks immediately without expanding further, preventing exponential search explosion.
            *   **Tie-Breaking Priority**: The priority queue sorts states by:
                $$\\text{Priority} = \\left(f(n), h(n), \\text{MRV Candidates}, \\text{State ID}\\right)$$
                This prioritizes deeper nodes with high constraints first, accelerating search to a solution.
            """
        )

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #64748b; font-size: 14px; margin-bottom: 20px;">'
    'Created for College Project Presentation &middot; Built with Python, Streamlit, and A* Search Heuristics'
    '</div>',
    unsafe_allow_html=True
)
