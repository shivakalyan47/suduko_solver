# 🧩 Intelligent Sudoku Solver Agent

A premium, interactive **Progressive Web Application (PWA)** built with Python and Streamlit, featuring an intelligent agent that solves and analyzes Sudoku puzzles. The agent models Sudoku as a **Constraint Satisfaction Problem (CSP)** and implements graph search and pathfinding paradigms to solve puzzles either instantly or through step-by-step visual exploration.

---

## 🚀 Key Features

### 🤖 1. AI Solver Mode
Select between two advanced solving paradigms, adjust the execution delay, and watch the agent navigate the search space:
*   **A* Graph Search**: Formulates Sudoku as a pathfinding problem. It evaluates grid states using a custom priority metric:
    $$f(n) = g(n) + h(n)$$
    *   $g(n)$ (Path Cost): Number of digits filled since the starting puzzle.
    *   $h(n)$ (Heuristic Cost): Number of remaining empty cells.
    *   **Tie-Breaking**: Explores states sorted by $f(n)$ (constant), $h(n)$ ascending, and Minimum Remaining Values (MRV) candidate count. This directs the A* agent along the most promising depth-first branches.
*   **Recursive Backtracking DFS**: An in-place recursive Depth-First Search solver. It operates directly on a single board instance to eliminate memory allocation and deep-copy overhead, rendering it extremely fast.
*   **Multi-Algorithm Benchmark Comparison**: Under identical starting grid conditions, the agent runs both A* and Backtracking DFS instantly, presenting comparative metrics for **Execution Time**, **Explored States**, **Search Velocity (states/sec)**, and **Efficiency Insights**.

### ✍️ 2. Play Manually Mode
For users who wish to solve the puzzle themselves:
*   **Keystroke Validation**: Programmatically restricts cell entries using custom-injected vanilla JavaScript. Only digits `1-9` are accepted; letters, symbols, duplicate keys, and invalid copy-pasting are intercepted and blocked.
*   **Check Progress (Solvability Checker)**: Evaluates the grid's mathematical viability in the background. It alerts the player if the current configuration is unsolvable, even if no immediate row/column/box conflicts exist.
*   **Smart Hints (MRV-Driven)**: Employs the **Minimum Remaining Values (MRV)** constraint heuristic to detect the emptiest cell with the fewest possibilities, placing the correct number and highlighting the cell with an amber/gold inset glow.

### 📱 3. Progressive Web App (PWA) Support
*   **Installable App**: Includes a Service Worker (`sw.js`) and Web App Manifest (`pwa_manifest.json`) allowing the dashboard to be installed on Android, iOS, Windows, or macOS, and run directly from the homescreen.
*   **Dynamic Asset Injection**: Automatically handles copying PWA manifest, service workers, and app icons into Streamlit's internal static build directories at runtime.
*   **Vite Dynamic Import Self-Healing**: Detects React/Vite dynamic import caching errors (`TypeError: Failed to fetch dynamically imported module`) and automatically performs a clean, throttle-protected cache reload to ensure app stability.

### 🎨 4. Premium Modern Aesthetics
*   **Glassmorphic Cards**: Sleek panel containers with backdrop blurring, subtle border lines, and soft shadows.
*   **Dual Light/Dark Adaptations**: Automatically reads prefers-color-scheme tokens to render matching backgrounds, inputs, and borders.
*   **Checkerboard Grouping**: Grid shading dynamically groups 3x3 Sudoku sub-grids for clear spatial scanning.
*   **Animated Visual Feedback**: Smooth fade-in alerts, active cell pulsing animations, and custom borders.

---

## 🛠️ Tech Stack & Requirements

*   **Core**: Python 3.8+
*   **Interface**: [Streamlit](https://streamlit.io/) (Fast interactive web application dashboard)
*   **Math Utilities**: Numpy
*   **Styling**: Custom CSS and Vanilla Javascript (HTML script injection)
*   **Testing**: Python standard `unittest` library

---

## 📂 Project Architecture

```bash
IAI single/
├── .git/                 # Git repository files
├── .gitignore            # Files excluded from version control
├── app.py                # Main web application entry point & UI dashboard
├── solver.py             # Core Sudoku solving algorithms and heuristic logic
├── style.css             # Premium CSS stylesheets & interactive hover styles
├── sw.js                 # Service worker definition for offline PWA capabilities
├── pwa_manifest.json     # PWA app parameters, theme colors, and icons
├── pwa_icon.png          # App icon used for PWA installation
├── requirements.txt      # Python library dependencies
└── test_solver.py        # Comprehensive suite of unit tests for the solver engine
```

---

## ⚙️ Setup & Installation

Follow these steps to run the application locally:

### 1. Clone or Download the Workspace
Navigate to your target workspace directory:
```bash
cd "c:\Users\shiva\Downloads\AAT\IAI single"
```

### 2. Install Dependencies
Install Streamlit and Numpy using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
Run the Streamlit app:
```bash
streamlit run app.py
```
This will start the local server and automatically open the application in your browser (typically at `http://localhost:8501`).

---

## 🔬 Running Unit Tests

A comprehensive suite of unit tests is included inside [test_solver.py](file:///c:/Users/shiva/Downloads/AAT/IAI%20single/test_solver.py) to verify the solver engine's features (such as board validation, candidate options retrieval, MRV picker, and puzzle solvers).

Run the tests using Python's standard `unittest` command:
```bash
python -m unittest test_solver.py
```

All 6 test suites will run and verify correctness:
*   `test_board_validation`: Verifies rows, columns, and 3x3 sub-grid duplicates.
*   `test_get_candidates`: Confirms cell candidate option calculation.
*   `test_mrv_cell_picker`: Validates selecting cells with the Minimum Remaining Values.
*   `test_solve_easy_puzzle`: Verifies the A* generator solves easy puzzles.
*   `test_solve_medium_puzzle`: Verifies the A* generator solves medium puzzles.
*   `test_impossible_puzzle`: Confirms unsolvable boards are correctly identified.

---

## 🧠 Solvers & Heuristics Deep Dive

### 1. Constraint Satisfaction & Fail-Fast Pruning
Sudoku is classified as a Constraint Satisfaction Problem. The solver ensures correctness at each branch depth by checking valid options before inserting them. When a branch arrives at an empty cell with **zero candidates**, the algorithm terminates that branch early (fails fast) and backtracks, preventing a combinatorial explosion.

### 2. Minimum Remaining Values (MRV)
Instead of scanning cells sequentially (e.g., top-to-bottom, left-to-right), the agent selects the cell that is the **most constrained** (i.e., has the smallest number of valid possibilities). This drastically decreases the branching factor of the search tree, allowing backtracking DFS to solve even the most complex puzzles (like the AI Escargot or Inkala's World's Hardest Sudoku) in under 1 millisecond.
