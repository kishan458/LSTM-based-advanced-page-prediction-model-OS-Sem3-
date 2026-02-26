import streamlit as st
import torch
import torch.nn as nn
import struct
import time
import plotly.graph_objects as go
from multiprocessing import shared_memory
from collections import OrderedDict

PAGE_SIZE = 4096

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="Hybrid Memory Monitor", layout="wide")

st.markdown("""
    <style>
    h1 { color: #0077ff; text-align: center; font-family: 'Segoe UI', sans-serif; margin-bottom: 0px; }
    .stMetric { background: rgba(0, 119, 255, 0.05); border: 1px solid #0077ff33; border-radius: 8px; }
    </style>
    <h1>🧠 Hybrid Memory Analytics</h1>
    <p style="text-align:center; color:#9d00ff; font-weight:bold; margin-top:0px;">Standard LRU vs. LSTM-Augmented Hybrid LRU</p>
    """, unsafe_allow_html=True)

# ---------------- ML MODEL ----------------
class MemoryLSTM(nn.Module):
    def _init_(self):
        super()._init_()
        self.lstm = nn.LSTM(1, 64, batch_first=True)
        self.fc = nn.Linear(64, 1)
    def forward(self, x):
        _, (h, _) = self.lstm(x)
        return self.fc(h[-1])

def get_pfn(pid, vaddr):
    try:
        page = vaddr // PAGE_SIZE
        with open(f"/proc/{pid}/pagemap", "rb") as f:
            f.seek(page * 8)
            entry = struct.unpack("Q", f.read(8))[0]
            if entry & (1 << 63): return entry & ((1 << 55) - 1)
    except: pass
    return None

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ System Control")
    LRU_CACHE_SIZE = st.slider("Cache Size (Frames)", 4, 128, 16)
    st.divider()
    
    st.header("🔍 Process Config")
    processes = []
    for i in range(3):
        st.markdown(f"*Process {i+1}*")
        pid = st.text_input("PID", key=f"pid{i}")
        offset = st.text_input("OFFSET (hex)", key=f"off{i}")
        shm_name = st.text_input("SHM name", key=f"shm{i}")
        processes.append((pid, offset, shm_name))
        st.divider()

if "proc_state" not in st.session_state:
    st.session_state.proc_state = {}

cols = st.columns(3)
cards = [{"header": st.empty(), "metrics": st.empty(), "text": st.empty(), "graph": st.empty()} for _ in range(3)]

# ---------------- MAIN LOOP ----------------
while True:
    for i, (pid_str, offset_str, shm_name) in enumerate(processes):
        if not pid_str or not offset_str or not shm_name:
            cards[i]["header"].info("Waiting for data...")
            continue

        try:
            pid = int(pid_str)
            base = int(offset_str, 16)
            shm = shared_memory.SharedMemory(name=shm_name)
            page = int.from_bytes(shm.buf[:4], "little")
        except:
            cards[i]["header"].error("SHM Sync Error")
            continue

        if pid not in st.session_state.proc_state:
            model = MemoryLSTM()
            st.session_state.proc_state[pid] = {
                "pages": [], "preds": [], "strides": [], "last": None, "last_seen": -1,
                "lru_std": OrderedDict(), "hits_std": 0,
                "lru_hybrid": OrderedDict(), "hits_hybrid": 0,
                "total": 0, "model": model, 
                "opt": torch.optim.Adam(model.parameters(), lr=0.01)
            }

        d = st.session_state.proc_state[pid]
        if page == d["last_seen"]: continue
        
        # --- DATA UPDATE ---
        d["total"] += 1
        stride = 0 if d["last"] is None else (page - d["last"])
        
        # 1. Standard LRU (Reactive)
        if page in d["lru_std"]:
            d["hits_std"] += 1
            d["lru_std"].move_to_end(page)
        else:
            if len(d["lru_std"]) >= LRU_CACHE_SIZE: d["lru_std"].popitem(last=False)
            d["lru_std"][page] = True

        # 2. Hybrid LRU (Checks if current page was pre-fetched or already in cache)
        if page in d["lru_hybrid"]:
            d["hits_hybrid"] += 1
            d["lru_hybrid"].move_to_end(page)
        else:
            if len(d["lru_hybrid"]) >= LRU_CACHE_SIZE: d["lru_hybrid"].popitem(last=False)
            d["lru_hybrid"][page] = True

        # --- LSTM PREDICTION & TRAINING ---
        hist = d["strides"][-6:]
        hist = [0] * (6 - len(hist)) + hist
        x = torch.tensor([hist], dtype=torch.float32).view(1, 6, 1)
        
        with torch.no_grad():
            pred_stride = int(round(d["model"](x).item()))
            pred_next_page = page + pred_stride
            d["preds"].append(pred_next_page)
        
        # PRE-FETCH: Inject the prediction into the HYBRID cache only
        if pred_next_page not in d["lru_hybrid"]:
            if len(d["lru_hybrid"]) >= LRU_CACHE_SIZE: d["lru_hybrid"].popitem(last=False)
            d["lru_hybrid"][pred_next_page] = True

        # Train LSTM
        d["model"].train()
        d["opt"].zero_grad()
        nn.MSELoss()(d["model"](x), torch.tensor([[float(stride)]])).backward()
        d["opt"].step()

        # Update State
        d["last"] = page
        d["last_seen"] = page
        d["pages"].append(page)
        d["strides"].append(stride)

        # --- UI UPDATE ---
        total = d["total"]
        pfn = get_pfn(pid, base + page * PAGE_SIZE)

        cards[i]["header"].markdown(f"### 📡 PID: ⁠ {pid} ⁠")
        cards[i]["metrics"].markdown(f"""
            *Standard LRU Hit Rate:* ⁠ {(100*d["hits_std"]/total):.1f}% ⁠  
            *Hybrid LRU Hit Rate:* ⁠ {(100*d["hits_hybrid"]/total):.1f}% ⁠  
            """)
        
        # Dual-Line Graph (Actual vs Predicted)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=d["pages"][-40:], mode='lines+markers', name='Actual', line=dict(color='#0077ff', width=3)))
        fig.add_trace(go.Scatter(y=d["preds"][-41:-1], mode='lines', name='LSTM Pred', line=dict(color='#9d00ff', width=2, dash='dot')))
        
        fig.update_layout(template="plotly_dark", height=260, margin=dict(l=0,r=0,t=10,b=0),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        
        cards[i]["graph"].plotly_chart(fig, use_container_width=True)
        cards[i]["text"].markdown(f"*PFN:* ⁠ {hex(pfn) if pfn else 'N/A'} ⁠ | *Page:* ⁠ {page} ⁠")

    time.sleep(0.1)