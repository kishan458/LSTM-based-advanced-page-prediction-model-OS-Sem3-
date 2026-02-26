<div align="center">
  <h1> Hybrid Memory Analytics</h1>
  <p><b>LSTM-Augmented Page Prediction & Cache Optimization</b></p>
  <p><i>A Deep Learning approach to proactive memory management and demand paging.</i></p>
</div>

<hr />

<h2> Project Overview</h2>
<p>
  The <b>LSTM-based Advanced Page Prediction Model</b> is a high-performance memory management simulation. It bridges low-level <b>C system programming</b> with <b>Recurrent Neural Networks (RNN)</b>. By monitoring a process's memory access patterns in real-time, the system uses an LSTM model to predict future page requests and "pre-fetch" them into a <b>Hybrid LRU Cache</b>.
</p>



<h2> Key Features</h2>
<ul>
  <li><b>⚡Real-Time Paging:</b> Monitors active processes via <code>/proc/[pid]/pagemap</code> to extract Physical Frame Numbers (PFN).</li>
  <li><b>LSTM Predictive Engine:</b> A PyTorch-powered model that learns memory "strides" to forecast the next page trajectory.</li>
  <li><b>Hybrid LRU Logic:</b> Compares a <b>Standard LRU</b> (reactive) against an <b>LSTM-Augmented LRU</b> (proactive).</li>
  <li><b>Live Analytics:</b> A Streamlit dashboard featuring real-time Plotly charts for Actual vs. Predicted access.</li>
  <li><b>IPC Integration:</b> Uses POSIX Shared Memory (<code>shm_open</code>) for ultra-low latency data syncing between C and Python.</li>
</ul>

<hr />

<h2> Tech Stack</h2>
<table width="100%">
  <tr>
    <th>Layer</th>
    <th>Technologies</th>
  </tr>
  <tr>
    <td><b>Frontend / UI</b></td>
    <td>Streamlit, Plotly (Dynamic Graphing)</td>
  </tr>
  <tr>
    <td><b>AI Core</b></td>
    <td>PyTorch (LSTM), Adam Optimizer, MSE Loss</td>
  </tr>
  <tr>
    <td><b>System Logic</b></td>
    <td>C (POSIX Shared Memory, mmap, Pagemap)</td>
  </tr>
  <tr>
    <td><b>Data Handling</b></td>
    <td>Python Shared Memory, Struct, OrderedDict</td>
  </tr>
</table>

<hr />

<h2>📂 Project Structure</h2>
<pre>
LSTM-Page-Predictor/
├── main.py           # Streamlit Dashboard & LSTM Training Loop
├── target.c          # C simulator (generates memory access patterns)
├── target            # Compiled binary for the Linux environment
└── README.md         # Documentation
</pre>

<hr />

<h2> Results & Performance Analysis</h2>
<p>The system evaluates performance based on the <b>Cache Hit Rate</b> across different memory access behaviors:</p>

<table>
  <tr>
    <th>Pattern Type</th>
    <th>Standard LRU</th>
    <th>Hybrid (LSTM) LRU</th>
    <th>Improvement</th>
  </tr>
  <tr>
    <td><b>Sequential (Stride 1)</b></td>
    <td>High</td>
    <td>Near 100%</td>
    <td>Predicts next page perfectly.</td>
  </tr>
  <tr>
    <td><b>Cyclic (Repeating Strides)</b></td>
    <td>Moderate</td>
    <td>High</td>
    <td>LSTM learns the loop frequency.</td>
  </tr>
  <tr>
    <td><b>Stochastic (Randomized)</b></td>
    <td>Low</td>
    <td>Low/Moderate</td>
    <td>Limited by pattern entropy.</td>
  </tr>
</table>

<blockquote>
  <b>Observation:</b> The Hybrid model excels in <i>strided access patterns</i> common in matrix operations and large-scale data processing, where the LSTM can predict the "jump" before the CPU executes the next instruction.
</blockquote>

<hr />

<h2>⚙️ Local Setup Instructions</h2>

<h3>1. Compile the Target</h3>
<p>Compile the C simulator on a Linux system:</p>
<code>gcc target.c -o target -lrt</code>

<h3>2. Install Dependencies</h3>
<code>pip install streamlit torch plotly</code>

<h3>3. Execution</h3>
<ol>
  <li>Start the simulator: <code>./target 1</code> (Note the PID and SHM name).</li>
  <li>Launch the UI: <code>streamlit run main.py</code></li>
  <li>Enter the PID in the sidebar to begin real-time tracking.</li>
</ol>

<hr />

<div align="center">
  <p>Built for Research in Operating Systems & Machine Learning</p>
</div>
