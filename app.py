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
    count_empty_cells,
    get_mrv_cell
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

            # Remove old PWA tags if they exist to allow updates to the PWA tag block
            if "<!-- PWA Installation Support -->" in content:
                start_idx = content.find("<!-- PWA Installation Support -->")
                end_idx = content.find("</script>", start_idx)
                if end_idx != -1:
                    content = content[:start_idx] + content[end_idx + len("</script>"):]

            # Add updated PWA tags if not present
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
      // Self-healing reload for Vite dynamic import errors
      const reloadOnImportError = (msg) => {
        if (msg && (msg.includes('dynamically imported module') || msg.includes('Failed to fetch'))) {
          const lastReload = sessionStorage.getItem('last_pwa_reload');
          const now = Date.now();
          if (!lastReload || now - parseInt(lastReload, 10) > 10000) {
            sessionStorage.setItem('last_pwa_reload', now.toString());
            window.location.reload();
          }
        }
      };
      window.addEventListener('error', (e) => reloadOnImportError(e.message || (e.error && e.error.message)), true);
      window.addEventListener('unhandledrejection', (e) => reloadOnImportError(e.reason && e.reason.message));

      // DOM fallback observer to catch errors captured and displayed by React's Error Boundary
      const checkDomForError = () => {
        const bodyText = document.body ? document.body.textContent : '';
        if (bodyText.includes('Failed to fetch dynamically imported module') || 
            bodyText.includes('TypeError: Failed to fetch')) {
          reloadOnImportError('dynamically imported module');
        }
      };
      setInterval(checkDomForError, 1000);

      if ('serviceWorker' in navigator) {
        // Reload page when the new service worker takes over and purges cache
        let refreshing = false;
        navigator.serviceWorker.addEventListener('controllerchange', () => {
          if (!refreshing) {
            refreshing = true;
            window.location.reload();
          }
        });

        window.addEventListener('load', () => {
          navigator.serviceWorker.register('./sw.js')
            .then(reg => {
              console.log('PWA Service Worker registered successfully!', reg);
              // Proactively check for updates on load
              reg.update();
            })
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

# Read and Inject style.css and dynamic board layout styles
CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css_content = f.read()
    
    # Generate exact cell CSS for border boundaries and checkerboard colors
    dynamic_css = []
    for r in range(9):
        for c in range(9):
            border_right = "4px solid #475569" if c in [2, 5] else ("none" if c == 8 else "1px solid #475569")
            border_bottom = "4px solid #475569" if r in [2, 5] else ("none" if r == 8 else "1px solid #475569")
            box_r, box_c = r // 3, c // 3
            bg_color = "#1e293b" if (box_r + box_c) % 2 == 0 else "#0f172a"
            
            dynamic_css.append(f"""
            .st-key-cell_input_{r}_{c} [data-testid="stTextInputRootElement"] {{
                background-color: {bg_color} !important;
                border-right: {border_right} !important;
                border-bottom: {border_bottom} !important;
                border-left: none !important;
                border-top: none !important;
                border-radius: 0px !important;
            }}
            .st-key-cell_input_{r}_{c} [data-testid="stTextInputRootElement"]:hover {{
                background-color: #2b394f !important;
            }}
            .st-key-cell_input_{r}_{c} [data-testid="stTextInputRootElement"]:focus-within {{
                background-color: #334155 !important;
                box-shadow: inset 0 0 5px rgba(20, 184, 166, 0.4) !important;
            }}
            """)
            
    combined_css = css_content + "\n" + "\n".join(dynamic_css)
    st.markdown(f"<style>{combined_css}</style>", unsafe_allow_html=True)
else:
    st.warning("Custom CSS file not found. Falling back to default Streamlit styles.")

# Helper to sync input cells back to session state board
def sync_input_to_board():
    version = st.session_state.get("widget_version", 0)
    for r in range(9):
        for c in range(9):
            key = f"cell_input_{r}_{c}_{version}"
            if key in st.session_state:
                val_str = st.session_state[key].strip()
                if val_str.isdigit() and 1 <= int(val_str) <= 9:
                    st.session_state.board[r][c] = int(val_str)
                else:
                    st.session_state.board[r][c] = 0

# Helper to force-sync session state widget inputs from the actual board representation
# This overrides Streamlit's internal widget caching bug!
def update_inputs_from_board():
    version = st.session_state.get("widget_version", 0)
    for r in range(9):
        for c in range(9):
            key = f"cell_input_{r}_{c}_{version}"
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
    st.session_state.widget_version += 1
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
    st.session_state.widget_version += 1
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
    st.session_state.solving_status = "idle" # idle, running, solved, unsolvable, invalid, user_solved, user_conflicts, user_solvable, user_unsolvable
if "active_cell" not in st.session_state:
    st.session_state.active_cell = None
if "is_visualizing" not in st.session_state:
    st.session_state.is_visualizing = False
if "solving_mode" not in st.session_state:
    st.session_state.solving_mode = "🤖 AI Solver"
if "play_message" not in st.session_state:
    st.session_state.play_message = ""
if "widget_version" not in st.session_state:
    st.session_state.widget_version = 0

# Sidebar Controls
with st.sidebar:
    with st.container(border=True):
        st.markdown("## ⚙️ Control Dashboard")
        
        # Mode selector
        mode_opt = st.radio(
            "🎮 Operation Mode",
            options=["🤖 AI Solver", "✍️ Play Manually"],
            key="solving_mode",
            help="🤖 AI Solver solves the Sudoku grid automatically. ✍️ Play Manually allows you to solve the puzzle yourself!"
        )
        st.markdown("---")
        
        # Preset puzzle selector with instant callback
        preset_opt = st.selectbox(
            "Select Preset Puzzle",
            options=list(PRESETS.keys()),
            index=0,
            key="preset_select",
            on_change=on_preset_change,
            help="Choose a pre-configured puzzle to load."
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
            st.session_state.widget_version += 1
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
            st.session_state.widget_version += 1
            update_inputs_from_board()
            st.rerun()
            
        st.markdown("---")
        
        # Display AI controls only in AI Solver mode
        if st.session_state.solving_mode == "🤖 AI Solver":
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
        else:
            # Fallback local bindings to avoid NameErrors in the main script
            algo_opt = "A* Search"
            delay = 0.05
        
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
            st.session_state.widget_version += 1
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
# Initialize button states to avoid NameErrors
visual_btn = False
instant_btn = False
verify_btn = False
progress_btn = False
hint_btn = False
reveal_all_btn = False

with st.container(border=True):
    st.markdown("### 🧩 Sudoku Board")
    
    # If currently solving/visualizing or solved, we show the read-only HTML visualizer.
    # Otherwise, we show interactive inputs for manual editing.
    show_html_visualizer = (
        st.session_state.is_visualizing or 
        (st.session_state.solving_mode == "🤖 AI Solver" and st.session_state.solving_status in ["solved", "unsolvable"])
    )
    
    if show_html_visualizer:
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
        
        # We render 9 rows of columns inside an inner container to enforce a rigid 9x9 layout structure
        with st.container(border=True):
            for r in range(9):
                cols = st.columns(9)
                for c in range(9):
                    with cols[c]:
                        val = st.session_state.board[r][c]
                        val_str = str(val) if val != 0 else ""
                        
                        st.text_input(
                            label=f"r{r}c{c}",
                            value=val_str,
                            max_chars=1,
                            key=f"cell_input_{r}_{c}_{st.session_state.get('widget_version', 0)}",
                            label_visibility="collapsed",
                            on_change=sync_input_to_board
                        )
    # Sync board from inputs before running
    sync_input_to_board()
    
    # Quick info about empty cells remaining
    empty_cnt = count_empty_cells(st.session_state.board)
    st.markdown(f'<span class="metric-badge">Empty Cells Remaining: {empty_cnt} / 81</span>', unsafe_allow_html=True)
    
    # Render controls depending on mode
    if st.session_state.solving_mode == "🤖 AI Solver":
        st.markdown("#### ⚡ AI Solver Controls")
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
    else:
        st.markdown("#### 🎮 Player Controls")
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        with btn_col1:
            verify_btn = st.button(
                "✅ Verify Solution",
                key="verify_solution_button",
                use_container_width=True
            )
        with btn_col2:
            progress_btn = st.button(
                "🔍 Check Progress",
                key="check_progress_button",
                use_container_width=True
            )
        with btn_col3:
            hint_btn = st.button(
                "💡 Reveal a Hint",
                key="reveal_hint_button",
                use_container_width=True
            )
        with btn_col4:
            reveal_all_btn = st.button(
                "👁️ Show Solution",
                key="show_solution_button",
                use_container_width=True
            )

# ------------------ SOLVER EXECUTION ------------------
if (visual_btn or instant_btn) and st.session_state.solving_mode == "🤖 AI Solver":
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
            st.session_state.widget_version += 1
            update_inputs_from_board()
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
            st.session_state.widget_version += 1
            update_inputs_from_board()
            st.rerun()

elif verify_btn and st.session_state.solving_mode == "✍️ Play Manually":
    if not is_valid_board(st.session_state.board):
        st.session_state.solving_status = "user_conflicts"
        st.session_state.play_message = "❌ There are duplicate numbers in rows, columns, or 3x3 blocks. Please resolve conflicts."
    else:
        empty_cnt = count_empty_cells(st.session_state.board)
        if empty_cnt > 0:
            st.session_state.solving_status = "user_conflicts"
            st.session_state.play_message = f"❌ The grid is not fully completed yet! There are still {empty_cnt} empty cells."
        else:
            st.session_state.solving_status = "user_solved"
            st.session_state.play_message = "🎉 Congratulations! You solved the Sudoku puzzle perfectly!"
    st.rerun()

elif progress_btn and st.session_state.solving_mode == "✍️ Play Manually":
    if not is_valid_board(st.session_state.board):
        st.session_state.solving_status = "user_conflicts"
        st.session_state.play_message = "⚠️ There are conflicts in your grid! Check for duplicate numbers in rows, columns, or 3x3 blocks."
    else:
        empty_cnt = count_empty_cells(st.session_state.board)
        if empty_cnt == 0:
            st.session_state.solving_status = "user_solved"
            st.session_state.play_message = "🎉 Congratulations! The grid is already solved perfectly!"
        else:
            # Check solvability using fast backtracking solver on a copy
            board_copy = copy.deepcopy(st.session_state.board)
            explored_ref = [0]
            solvable = solve_sudoku_backtracking_fast(board_copy, explored_ref)
            if solvable:
                st.session_state.solving_status = "user_solvable"
                st.session_state.play_message = "📈 Great job! All entered numbers are correct so far, and the board is solvable. Keep going!"
            else:
                st.session_state.solving_status = "user_unsolvable"
                st.session_state.play_message = "⚠️ Warning: No immediate conflicts, but this current configuration is mathematically unsolvable. One of your inputs is wrong!"
    st.rerun()

elif hint_btn and st.session_state.solving_mode == "✍️ Play Manually":
    if not is_valid_board(st.session_state.board):
        st.error("⚠️ Cannot provide a hint while there are conflicts on the board. Please resolve them first!")
    else:
        empty_cnt = count_empty_cells(st.session_state.board)
        if empty_cnt == 0:
            st.info("ℹ️ The Sudoku is already fully completed!")
        else:
            # Find the solution
            board_copy = copy.deepcopy(st.session_state.board)
            explored_ref = [0]
            solvable = solve_sudoku_backtracking_fast(board_copy, explored_ref)
            if solvable:
                # Find an MRV cell
                r, c, candidates = get_mrv_cell(st.session_state.board)
                if r is not None:
                    correct_val = board_copy[r][c]
                    st.session_state.board[r][c] = correct_val
                    st.session_state.solving_status = "user_solvable"
                    st.session_state.play_message = f"💡 Hint: Placed correct number {correct_val} at Row {r+1}, Column {c+1}!"
                    st.session_state.widget_version += 1
                    update_inputs_from_board()
                    st.rerun()
            else:
                st.session_state.solving_status = "user_unsolvable"
                st.session_state.play_message = "⚠️ The current board is unsolvable. Remove some numbers or reset to get a valid puzzle!"
                st.rerun()

elif reveal_all_btn and st.session_state.solving_mode == "✍️ Play Manually":
    if not is_valid_board(st.session_state.board):
        st.error("⚠️ Cannot solve because the starting board has conflicts!")
    else:
        board_copy = copy.deepcopy(st.session_state.board)
        explored_ref = [0]
        solvable = solve_sudoku_backtracking_fast(board_copy, explored_ref)
        if solvable:
            st.session_state.board = board_copy
            st.session_state.solving_status = "solved"
            st.session_state.solving_time = 0.0
            st.session_state.explored_states = explored_ref[0]
            st.session_state.widget_version += 1
            update_inputs_from_board()
            st.rerun()
        else:
            st.error("❌ The board configuration is mathematically unsolvable!")
            
# Display Solving Outcomes
if st.session_state.solving_status in ["solved", "unsolvable", "limit_reached", "user_solved", "user_conflicts", "user_solvable", "user_unsolvable"]:
    if st.session_state.solving_status == "solved":
        if st.session_state.solving_mode == "🤖 AI Solver":
            st.markdown(
                f'<div class="solved-alert">🎉 Success! Sudoku solved perfectly using {algo_opt} in {st.session_state.solving_time:.4f} seconds!</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="solved-alert">🎉 Sudoku solved successfully by the agent!</div>',
                unsafe_allow_html=True
            )
    elif st.session_state.solving_status == "unsolvable":
        st.error("❌ Unsolvable Sudoku! No valid configuration satisfies the constraints for this board.")
    elif st.session_state.solving_status == "limit_reached":
        st.warning("⚠️ Limit Reached! The search space exceeded the safe threshold without finding a solution.")
    elif st.session_state.solving_status == "user_solved":
        st.markdown(
            f'<div class="solved-alert">{st.session_state.play_message}</div>',
            unsafe_allow_html=True
        )
    elif st.session_state.solving_status == "user_conflicts":
        st.error(st.session_state.play_message)
    elif st.session_state.solving_status == "user_solvable":
        st.success(st.session_state.play_message)
    elif st.session_state.solving_status == "user_unsolvable":
        st.warning(st.session_state.play_message)
        
    # Run comparison instantly
    if st.session_state.solving_mode == "🤖 AI Solver" and st.session_state.solving_status in ["solved", "unsolvable", "limit_reached"]:
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
# 1. Performance / Game Metrics Card
with st.container(border=True):
    if st.session_state.solving_mode == "🤖 AI Solver":
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
    else:
        st.markdown("### 📊 Game Progress Metrics")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            empty_cells = count_empty_cells(st.session_state.board)
            st.metric(
                label="🧩 Filled Cells",
                value=f"{81 - empty_cells} / 81",
                delta=f"-{empty_cells} remaining" if empty_cells > 0 else "Fully Filled!"
            )
            # Find conflict status
            has_conflicts = not is_valid_board(st.session_state.board)
            st.metric(
                label="⚠️ Conflicting Entries",
                value="Yes (Duplicates Exist)" if has_conflicts else "None (Valid)",
                delta="Fix Conflicts!" if has_conflicts else "Keep going!"
            )
        with col_m2:
            status_badges = {
                "idle": "✏️ Playing / Editing",
                "user_solved": "🎉 Completed!",
                "user_conflicts": "❌ Conflicts Detected",
                "user_solvable": "🟢 Solvable",
                "user_unsolvable": "🟡 Unsolvable Grid",
                "solved": "👁️ Revealed Solution"
            }
            st.metric(
                label="📡 Game Status",
                value=status_badges.get(st.session_state.solving_status, "✏️ Playing / Editing")
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
        
        #### 4. How the AI Agent Assists the Manual Player
        In **Manual Play Mode**, the AI solver runs in the background whenever you check your progress or ask for a hint:
        *   **Check Progress**: Instantly clones the current board and runs the backtracking solver in-place. If it cannot find a valid solution, it alerts you that a wrong placement has been made, even if there are no immediate duplicates.
        *   **Reveal a Hint**: Uses the Minimum Remaining Values (MRV) constraint heuristic to identify the cell with the fewest candidate options, retrieves the correct number from the background-solved board, and automatically places it in the grid.
        """
    )

# Input validation script to restrict entering text (only digits 1-9 allowed)
st.html(
    """
    <script>
    // Helper to change input value programmatically in a React-friendly way
    const setReactInputValue = (input, value) => {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
        nativeInputValueSetter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
    };

    // Keydown event listener: block typing non-1-9 characters
    const cleanInputListener = (e) => {
        if (e.target && e.target.tagName === 'INPUT') {
            const cellWrapper = e.target.closest('[class*="st-key-cell_input_"]');
            if (cellWrapper) {
                if (e.ctrlKey || e.metaKey || e.altKey) {
                    return;
                }
                const allowedKeys = ['Backspace', 'Tab', 'Enter', 'Escape', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Delete'];
                if (allowedKeys.includes(e.key)) {
                    return;
                }
                // Only allow keys '1' to '9'
                if (e.key < '1' || e.key > '9') {
                    e.preventDefault();
                }
            }
        }
    };

    // Paste event listener: block pasting invalid text
    const pasteListener = (e) => {
        if (e.target && e.target.tagName === 'INPUT') {
            const cellWrapper = e.target.closest('[class*="st-key-cell_input_"]');
            if (cellWrapper) {
                const pasteData = (e.clipboardData || window.clipboardData).getData('text');
                if (!/^[1-9]$/.test(pasteData)) {
                    e.preventDefault();
                }
            }
        }
    };

    // Input event listener: strip invalid characters (virtual keyboard fallback)
    const inputListener = (e) => {
        if (e.target && e.target.tagName === 'INPUT') {
            const cellWrapper = e.target.closest('[class*="st-key-cell_input_"]');
            if (cellWrapper) {
                const val = e.target.value;
                const cleaned = val.replace(/[^1-9]/g, '');
                const finalVal = cleaned.length > 0 ? cleaned[0] : '';
                if (val !== finalVal) {
                    setReactInputValue(e.target, finalVal);
                }
            }
        }
    };

    // Helper to register listeners to a document
    const registerListeners = (doc) => {
        if (!doc) return;
        doc.removeEventListener('keydown', cleanInputListener, true);
        doc.addEventListener('keydown', cleanInputListener, true);
        doc.removeEventListener('paste', pasteListener, true);
        doc.addEventListener('paste', pasteListener, true);
        doc.removeEventListener('input', inputListener, true);
        doc.addEventListener('input', inputListener, true);
    };

    // Register on both local window and parent window (for inside iframes)
    registerListeners(document);
    registerListeners(window.parent.document);
    </script>
    """,
    unsafe_allow_javascript=True
)

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #64748b; font-size: 14px; margin-bottom: 20px;">'
    'Created for College Project Presentation &middot; Built with Python, Streamlit, and A* Search Heuristics'
    '</div>',
    unsafe_allow_html=True
)
