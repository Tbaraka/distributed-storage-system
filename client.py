
#  node.py  —  Mini Distributed Key-Value Store
#  Person 1: Node Server (handles GET / POST / DELETE)
# ============================================================
#
#  HOW TO RUN (open 3 separate terminals):
#    Terminal 1:  python node.py 5001
#    Terminal 2:  python node.py 5002
#    Terminal 3:  python node.py 5003
#
#  INSTALL DEPENDENCIES FIRST:
#    pip install flask requests


import sys
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------- Confixguration ----------
PORT  = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
ALL_PORTS = [5001, 5002, 5003]
PEERS = [p for p in ALL_PORTS if p != PORT]   # other nodes

# ---------- In-memory storage ----------
store = {}   # { "username": "group4", "course": "DST" ... }


# ============================================================
#  HELPER: forward a write to peer nodes
# ============================================================
def replicate_to_peers(method, key, value=None):
    """
    Send a write (POST or DELETE) to all peer nodes.
    We pass  replicate=false  so they save locally only
    and do NOT forward again — prevents infinite loops.
    """
    for peer_port in PEERS:
        url = f"http://127.0.0.1:{peer_port}/keys/{key}?replicate=false"
        try:
            if method == "POST":
                requests.post(url, json={"value": value}, timeout=1)
            elif method == "DELETE":
                requests.delete(url, timeout=1)
        except Exception:
            # Peer is down — skip it, system stays available
            print(f"[Node {PORT}] Warning: could not reach peer {peer_port}")


# ============================================================
#  ROUTE 1:  GET /keys  — list all keys stored on this node
# ============================================================
@app.route("/keys", methods=["GET"])
def list_keys():
    return jsonify({
        "status": "ok",
        "node":   PORT,
        "keys":   list(store.keys()),
        "count":  len(store)
    }), 200


# ============================================================
#  ROUTE 2:  GET /keys/<key>  — retrieve a value
# ============================================================
@app.route("/keys/<key>", methods=["GET"])
def get_key(key):
    if key not in store:
        return jsonify({"status": "error", "message": f"Key '{key}' not found"}), 404

    return jsonify({
        "status": "ok",
        "node":   PORT,
        "key":    key,
        "value":  store[key]
    }), 200


# ============================================================
#  ROUTE 3:  POST /keys/<key>  — store a value
#  Body (JSON):  { "value": "Teddy" }
# ============================================================
@app.route("/keys/<key>", methods=["POST"])
def put_key(key):
    data = request.get_json()

    # Validate request body
    if not data or "value" not in data:
        return jsonify({"status": "error", "message": "Request body must include 'value'"}), 400

    value     = data["value"]
    replicate = request.args.get("replicate", "true")   # "false" when called by a peer

    # Save locally
    store[key] = value
    print(f"[Node {PORT}] Stored  {key} = {value}")

    # Forward to peers (only if this is the original request)
    if replicate == "true":
        replicate_to_peers("POST", key, value)

    return jsonify({
        "status":    "ok",
        "node":      PORT,
        "key":       key,
        "value":     value,
        "replicated": replicate == "true"
    }), 201


# ============================================================
#  ROUTE 4:  DELETE /keys/<key>  — remove a value
# ============================================================
@app.route("/keys/<key>", methods=["DELETE"])
def delete_key(key):
    replicate = request.args.get("replicate", "true")

    if key not in store:
        return jsonify({"status": "error", "message": f"Key '{key}' not found"}), 404

    del store[key]
    print(f"[Node {PORT}] Deleted  {key}")

    if replicate == "true":
        replicate_to_peers("DELETE", key)

    return jsonify({
        "status": "ok",
        "node":   PORT,
        "key":    key,
        "message": f"Key '{key}' deleted"
    }), 200


# ============================================================
#  ROUTE 5:  GET /status  — node health check
# ============================================================
@app.route("/status", methods=["GET"])
def status():
    peer_status = {}
    for peer_port in PEERS:
        try:
            r = requests.get(f"http://127.0.0.1:{peer_port}/status", timeout=1)
            peer_status[peer_port] = "online" if r.status_code == 200 else "error"
        except Exception:
            peer_status[peer_port] = "offline"

    return jsonify({
        "status":      "ok",
        "node":        PORT,
        "keys_stored": len(store),
        "peers":       peer_status
    }), 200


# ============================================================
#  Start the server
# ============================================================
if __name__ == "__main__":
    print(f"\n  Node {PORT} starting...")
    print(f"  Peers: {PEERS}")
    print(f"  Visit: http://127.0.0.1:{PORT}/status\n")
    app.run(port=PORT, debug=False)

    