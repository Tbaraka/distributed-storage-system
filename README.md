# 🗄️ Distributed Key-Value Store

> A mini distributed storage system built with Python and Flask.  
> Data is replicated across 3 nodes — if one goes down, the others keep running.

**Group 4 | DST4010A**  
Teddy Baraka · Derby Otieno · Joseph Santurino

---

## 📌 What Is This?

This project implements a **distributed key-value store** — a simple database spread across multiple servers (nodes). Every time you save a value, it automatically copies to all nodes. If one node crashes, your data is still accessible from the others.

Think of it like saving the same note in 3 different notebooks. Lose one notebook — you still have two copies.

### Key Features

- ✅ **REST API** — proper HTTP verbs (GET, POST, DELETE)
- ✅ **3-node replication** — every write copies to all peers automatically
- ✅ **Fault tolerant** — system keeps working when 1 node goes down
- ✅ **Health monitoring** — each node reports the status of its peers
- ✅ **Latency benchmarking** — built-in metrics script

---

## 🏗️ Architecture

```
         [ Client Script / REST Client ]
                      |
          POST /keys/{key}  {"value": "..."}
                      |
                      ▼
          ┌─────────────────────┐
          │     Node 1 :5001    │
          │  Flask + dict {}    │
          │  Replication Layer  │
          └──────┬──────────────┘
                 │
        replicate (POST/DELETE)
        with replicate=false
                 │
       ┌─────────┴──────────┐
       ▼                    ▼
┌─────────────┐     ┌─────────────┐
│ Node 2:5002 │     │ Node 3:5003 │
│ Flask+dict  │     │ Flask+dict  │
└─────────────┘     └─────────────┘
```

### How Replication Works

1. Client sends `POST /keys/username` to Node 1
2. Node 1 saves `username` to its local dictionary
3. Node 1 forwards the write to Node 2 and Node 3 with `replicate=false`
4. Peer nodes save locally — they do **not** forward again (prevents infinite loops)
5. Node 1 returns `201 Created` to the client

---

## 📁 Project Structure

```
distributed-kvstore/
│
├── node.py          # Flask node server — run 3 times on different ports
├── client.py        # Demo script — tests replication, fault tolerance & latency
├── metrics.py       # Benchmarking script — measures PUT/GET latency & availability
├── test.http        # REST Client test file — manual endpoint testing
└── README.md        # This file
```

---

## ⚙️ Requirements

- Python 3.8+
- Flask
- requests

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/distributed-kvstore.git
cd distributed-kvstore
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install flask requests
```

### 4. Start the 3 Nodes

Open **3 separate terminals** and run one command in each:

```bash
# Terminal 1
python3 node.py 5001

# Terminal 2
python3 node.py 5002

# Terminal 3
python3 node.py 5003
```

You should see this in each terminal:
```
Node 5001 starting...
Peers: [5002, 5003]
Visit: http://127.0.0.1:5001/status
```

### 5. Verify All Nodes Are Online

Open your browser and visit:
```
http://127.0.0.1:5001/status
```

Expected response:
```json
{
  "status": "ok",
  "node": 5001,
  "keys_stored": 0,
  "peers": {
    "5002": "online",
    "5003": "online"
  }
}
```

---

## 📡 API Reference

All nodes expose the same REST API. Replace `5001` with `5002` or `5003` to talk to a different node.

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/keys` | List all stored keys | 200 |
| `GET` | `/keys/{key}` | Retrieve a value | 200 / 404 |
| `POST` | `/keys/{key}` | Store a value (replicates) | 201 |
| `DELETE` | `/keys/{key}` | Remove a key (replicates) | 200 / 404 |
| `GET` | `/status` | Node health + peer status | 200 |

### Examples

**Store a value:**
```bash
curl -X POST http://127.0.0.1:5001/keys/username \
     -H "Content-Type: application/json" \
     -d '{"value": "Teddy"}'
```

**Read from any node (proves replication):**
```bash
curl http://127.0.0.1:5003/keys/username
```

**Delete a key:**
```bash
curl -X DELETE http://127.0.0.1:5001/keys/username
```

**Check node health:**
```bash
curl http://127.0.0.1:5001/status
```

---

## 🧪 Testing

### Run the Full Demo

The demo script automatically tests replication, fault tolerance, and latency:

```bash
python3 client.py
```

The demo walks through 5 sections:

| Section | What It Tests |
|---------|--------------|
| Demo 1 | Basic PUT and GET |
| Demo 2 | Replication — write to Node 1, read from Node 3 |
| Demo 3 | Fault tolerance — kill Node 2, data still accessible |
| Demo 4 | Node recovery — restart Node 2 |
| Demo 5 | Latency benchmark |

### Run the Metrics Script

```bash
python3 metrics.py
```

Outputs PUT latency, GET latency, replication consistency, and availability. Save results with:

```bash
python3 metrics.py | tee results.txt
```

### Manual Testing with REST Client

If you use the VS Code [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension, open `test.http` and click **Send Request** above any block.

---

## 📊 Benchmark Results

Results from a local macOS machine (3 nodes on localhost):

| Metric | Result |
|--------|--------|
| PUT Latency (avg) | 5.07 ms |
| PUT Latency (min / max) | 4.68 ms / 6.24 ms |
| GET Latency (avg) | 1.40 ms |
| GET Latency (min / max) | 1.31 ms / 1.51 ms |
| Replication Consistency | 3/3 nodes — 100% |
| System Availability | 30/30 requests — 100% |
| Replication Speed | 115.15 ms total |

> GET is ~3.6× faster than PUT because reads only hit the local dictionary with no replication overhead.

---

## 🔧 Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| API design | REST (proper HTTP verbs) | Semantically correct — GET should never modify data |
| Consistency model | Eventual consistency | Simpler than strong consistency; no locking required |
| Replication trigger | Eager (on every write) | Data spreads immediately; easy to demo and verify |
| Storage backend | In-memory Python dict | No setup; fast O(1) reads and writes |
| Failure handling | Timeout + skip peer | Keeps system available when a peer is unreachable |
| Communication | HTTP + JSON | Easy to test with browser, curl, or REST Client |

### CAP Theorem Position

This system is an **AP system** — it prioritises **Availability** and **Partition Tolerance** over strict Consistency. Nodes may briefly hold different values after a write, but the system always responds to requests.

---

## ⚠️ Known Limitations

- **No persistent storage** — data is lost when a node restarts (in-memory only)
- **No conflict resolution** — concurrent writes to the same key result in last-write-wins
- **No sync on recovery** — a restarted node has stale data until the next write updates it
- **No retry queue** — if a peer is down during replication, that write is not retried

---

## 🛣️ Future Improvements

- [ ] Add SQLite persistent storage so data survives restarts
- [ ] Add a `/sync` endpoint so recovered nodes can catch up with peers
- [ ] Implement a retry queue for failed replications
- [ ] Add leader election to resolve write conflicts
- [ ] Async replication to reduce PUT latency
- [ ] Add write-ahead logging for crash recovery

---

## 🗂️ Concepts Demonstrated

| Concept | Where |
|---------|-------|
| Key-value storage | `store = {}` in `node.py` |
| REST API design | All 5 routes in `node.py` |
| Eager replication | `replicate_to_peers()` in `node.py` |
| Fault tolerance | `try/except` with `timeout=1` |
| Eventual consistency | Node recovery demo in `client.py` |
| CAP theorem | AP system — availability over consistency |
| Health monitoring | `GET /status` route |
| Latency benchmarking | `metrics.py` |

---

## 📄 License

This project was built for educational purposes as part of the DST4010A Distributed Systems course.

---

> Built with Python 🐍 · Flask 🌶️ · April 2026
