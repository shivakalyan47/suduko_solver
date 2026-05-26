import streamlit as st
import time
import os
import copy
import shutil
from solver import (
    solve_sudoku_astar_generator,
    solve_sudoku_backtracking_generator,
    solve_sudoku_backtracking_fast,
    PRESETS,
    is_valid_board,
    generate_random_puzzle_board,
    count_empty_cells
)

# Automatic runtime PWA asset injection and setup!
# This ensures it works both locally on PC and hosted in the cloud (Streamlit Cloud)!
def inject_pwa_assets():
    try:
        # Locate the static assets directory of the active Streamlit library installation
        static_dir = os.path.join(os.path.dirname(st.__file__), "static")
        if not os.path.exists(static_dir):
            return

        workspace_dir = os.path.dirname(__file__)
        
        # Define PWA assets inside our workspace
        src_manifest = os.path.join(workspace_dir, "pwa_manifest.json")
        src_sw = os.path.join(workspace_dir, "sw.js")
        src_icon = os.path.join(workspace_dir, "pwa_icon.png")

        dest_manifest = os.path.join(static_dir, "pwa_manifest.json")
        dest_sw = os.path.join(static_dir, "sw.js")
        dest_icon = os.path.join(static_dir, "pwa_icon.png")

        # Copy the custom icon, manifest, and service worker to static assets
        if os.path.exists(src_icon):
            shutil.copy2(src_icon, dest_icon)
        if os.path.exists(src_manifest):
            shutil.copy2(src_manifest, dest_manifest)
        if os.path.exists(src_sw):
            shutil.copy2(src_sw, dest_sw)

        # Inject PWA configuration links and scripts into active index.html
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Overwrite default index title
            if "<title>Streamlit</title>" in content:
                content = content.replace("<title>Streamlit</title>", "<title>Sudoku Solver</title>")

            # Add PWA tags if not present
            if "pwa_manifest.json" not in content:
                pwa_tags = """
    <!-- PWA Installation Support -->
    <link rel="manifest" href="./pwa_manifest.json" />
    <meta name="theme-color" content="#6366f1" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="default" />
    <meta name="apple-mobile-web-app-title" content="Sudoku Solver" />
    <link rel="apple-touch-icon" href="./pwa_icon.png" />
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('./sw.js')
            .then(reg => console.log('PWA Service Worker registered successfully!', reg))
            .catch(err => console.log('PWA Service Worker registration failed:', err));
        });
      }
    </script>
"""
                if "<head>" in content:
                    content = content.replace("<head>", "<head>" + pwa_tags)

            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        pass

# Run injection immediately
inject_pwa_assets()

# Page Configuration
st.set_page_config(
    page_title="Sudoku Solver",
    page_icon=os.path.join(os.path.dirname(__file__), "pwa_icon.png") if os.path.exists(os.path.join(os.path.dirname(__file__), "pwa_icon.png")) else "🧩",
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
        st.markdown("---")
        
        # Algorithm Selector
        algo_opt = st.selectbox(
            "🧠 Select AI Algorithm",
            options=["A* Search", "Backtracking DFS"],
            index=0,
            help="A* Search uses heuristics and path cost inside a priority queue. Backtracking DFS performs a recursive in-place search."
        )
        
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

# Helper to run both solvers instantly and return comparison stats
def get_algorithm_comparison(initial_board):
    # 1. Measure A* Search
    board_astar = copy.deepcopy(initial_board)
    start_astar = time.time()
    generator_astar = solve_sudoku_astar_generator(board_astar)
    final_status = "unsolvable"
    final_explored = 0
    for curr_board, active_cell, explored_count, status in generator_astar:
        final_status = status
        final_explored = explored_count
    time_astar = time.time() - start_astar
    explored_astar = final_explored
    status_astar = "Solved" if final_status == "solved" else "Unsolvable"
    
    # 2. Measure Backtracking DFS
    board_backtrack = copy.deepcopy(initial_board)
    start_backtrack = time.time()
    explored_ref = [0]
    solved_backtrack = solve_sudoku_backtracking_fast(board_backtrack, explored_ref)
    time_backtrack = time.time() - start_backtrack
    explored_backtrack = explored_ref[0]
    status_backtrack = "Solved" if solved_backtrack else "Unsolvable"
    
    return {
        "A* Search": {"time": max(time_astar, 0.00001), "states": explored_astar, "status": status_astar},
        "Backtracking DFS": {"time": max(time_backtrack, 0.00001), "states": explored_backtrack, "status": status_backtrack}
    }

# Main Application Layout
st.markdown('<h1 style="text-align: center;"><span class="gradient-text">🧩 Intelligent Sudoku Solver Agent</span><br><small style="font-size: 16px; font-weight: 400; color: #64748b;">Powered by A* Search & Constraint Propagation</small></h1>', unsafe_allow_html=True)

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

# ----------------- MAIN FEED: Board & Solve buttons -----------------
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
            if algo_opt == "A* Search":
                generator = solve_sudoku_astar_generator(st.session_state.board)
            else:
                generator = solve_sudoku_backtracking_generator(st.session_state.board)
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
            start_time = time.time()
            if algo_opt == "A* Search":
                generator = solve_sudoku_astar_generator(st.session_state.board)
                final_board = None
                final_status = "unsolvable"
                final_explored = 0
                
                for curr_board, active_cell, explored_count, status in generator:
                    final_board = curr_board
                    final_status = status
                    final_explored = explored_count
            else:
                # Pure backtracking fast solver (super optimized in-place search!)
                explored_ref = [0]
                board_copy = copy.deepcopy(st.session_state.board)
                solved = solve_sudoku_backtracking_fast(board_copy, explored_ref)
                if solved:
                    final_board = board_copy
                    final_status = "solved"
                else:
                    final_board = st.session_state.board
                    final_status = "unsolvable"
                final_explored = explored_ref[0]
                
            st.session_state.board = final_board if final_board else st.session_state.board
            st.session_state.solving_status = final_status
            st.session_state.explored_states = final_explored
            st.session_state.solving_time = time.time() - start_time
            st.session_state.is_visualizing = False
            st.session_state.active_cell = None
            st.rerun()
            
# Display Solving Outcomes
if st.session_state.solving_status in ["solved", "unsolvable", "limit_reached"]:
    if st.session_state.solving_status == "solved":
        st.markdown(
            f'<div class="solved-alert">🎉 Success! Sudoku solved perfectly using {algo_opt} in {st.session_state.solving_time:.4f} seconds!</div>',
            unsafe_allow_html=True
        )
    elif st.session_state.solving_status == "unsolvable":
        st.error("❌ Unsolvable Sudoku! No valid configuration satisfies the constraints for this board.")
    elif st.session_state.solving_status == "limit_reached":
        st.warning("⚠️ Limit Reached! The search space exceeded the safe threshold without finding a solution.")
        
    # Run comparison instantly
    comp_data = get_algorithm_comparison(st.session_state.original_board)
    
    # Display the comparison card
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 📊 Multi-Algorithm Performance Comparison")
        st.caption("Under identical starting grid conditions, the agent evaluated both algorithms instantly to compile these metrics:")
        
        # Construct a beautiful HTML Table with glassmorphic styles
        html_table = f"""
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-family: 'Outfit', sans-serif;">
            <thead>
                <tr style="border-bottom: 2px solid rgba(148, 163, 184, 0.3); text-align: left;">
                    <th style="padding: 12px; font-weight: 600;">🧠 AI Algorithm</th>
                    <th style="padding: 12px; font-weight: 600;">⏱️ Execution Time</th>
                    <th style="padding: 12px; font-weight: 600;">🔬 Explored States</th>
                    <th style="padding: 12px; font-weight: 600;">⚡ Search Velocity</th>
                    <th style="padding: 12px; font-weight: 600;">📡 Status</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(148, 163, 184, 0.15);">
                    <td style="padding: 12px; font-weight: 600; color: #8b5cf6;">A* Search Agent</td>
                    <td style="padding: 12px; font-weight: 700;">{comp_data['A* Search']['time']:.5f} s</td>
                    <td style="padding: 12px;">{comp_data['A* Search']['states']:,} states</td>
                    <td style="padding: 12px; color: #64748b;">{int(comp_data['A* Search']['states'] / comp_data['A* Search']['time']) if comp_data['A* Search']['time'] > 0 else 0:,} st/s</td>
                    <td style="padding: 12px;"><span style="background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 2px 8px; font-size: 13px; font-weight: 600;">{comp_data['A* Search']['status']}</span></td>
                </tr>
                <tr>
                    <td style="padding: 12px; font-weight: 600; color: #14b8a6;">Recursive Backtracking (MRV)</td>
                    <td style="padding: 12px; font-weight: 700; color: #10b981;">{comp_data['Backtracking DFS']['time']:.5f} s</td>
                    <td style="padding: 12px;">{comp_data['Backtracking DFS']['states']:,} states</td>
                    <td style="padding: 12px; color: #64748b;">{int(comp_data['Backtracking DFS']['states'] / comp_data['Backtracking DFS']['time']) if comp_data['Backtracking DFS']['time'] > 0 else 0:,} st/s</td>
                    <td style="padding: 12px;"><span style="background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 2px 8px; font-size: 13px; font-weight: 600;">{comp_data['Backtracking DFS']['status']}</span></td>
                </tr>
            </tbody>
        </table>
        """
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Quick summary / insight message!
        speedup = comp_data['A* Search']['time'] / comp_data['Backtracking DFS']['time'] if comp_data['Backtracking DFS']['time'] > 0 else 1
        if speedup > 1.5:
            st.markdown(f"<div style='margin-top: 15px; font-size: 14px; color: #64748b;'>💡 <b>Agent Insight:</b> Backtracking DFS solved this puzzle <b>{speedup:.1f}x faster</b> than A* because mutating the grid in-place eliminates the overhead of node cloning and priority queue operations in pure Python.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='margin-top: 15px; font-size: 14px; color: #64748b;'>💡 <b>Agent Insight:</b> Both algorithms solved this puzzle rapidly, showcasing the high efficiency of the Minimum Remaining Values (MRV) constraint heuristics.</div>", unsafe_allow_html=True)

# ----------------- METRICS & WALKTHROUGH (Moved below controls) -----------------
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
        This agent supports two highly advanced AI solving paradigms:
        
        #### 1. A* Graph Search Formulation
        The A* algorithm evaluates grid states using the path and heuristic cost:
        $$f(n) = g(n) + h(n)$$
        
        *   **$g(n)$ (Path Cost)**: Number of digits filled since the starting puzzle.
        *   **$h(n)$ (Heuristic Cost)**: Number of remaining empty cells.
        *   **Tie-Breaking Priority**: Since $f(n)$ is a constant ($81 - K$) across any specific branch, the min-heap sorts states using:
            $$\\text{Priority} = (f(n), h(n), C, \\text{ID})$$
            Where $C$ is the count of MRV candidates, and $\\text{ID}$ is a unique state tie-breaker. This fits perfectly on all screens without overflowing!
            
        #### 2. Advanced Constraint Optimization Heuristics
        Both algorithms use Constraint Satisfaction Programming (CSP) rules:
        *   **Minimum Remaining Values (MRV)**: Selects the empty cell with the **absolute fewest valid numbers** remaining to minimize the search tree.
        *   **Fail-Fast Backtracking**: If any empty cell has **zero valid candidates**, the search path is instantly recognized as a dead-end and pruned, preventing exponential explosion.
        
        #### 3. Algorithm Comparison (A* vs Backtracking DFS)
        *   **A* Search**: Maintains a priority queue of multiple active search branches. While optimal for pathfinding, it creates copy overhead and sorting costs, making extremely complex seeds (like Inkala 2012) slower to solve in pure Python.
        *   **Backtracking DFS**: Traverses a single search path in-place recursively. Because it mutates and reverts the grid **in-place on a single object**, it has **zero deepcopy or heap sorting overhead**, solving the hardest puzzles instantly in a fraction of a millisecond!
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
