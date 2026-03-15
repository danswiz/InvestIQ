"""
Standalone Research API server — runs on Mac mini, called by Vercel frontend.
No timeout limits. Full verification pipeline.

Usage:
  python3 research_server.py          # runs on port 5050
  python3 research_server.py --port 8080

Frontend calls: POST https://<mac-mini>:5050/api/research/stream
"""

import json
import os
import queue
import threading
import traceback
import uuid
from datetime import datetime, timezone
from flask import Flask, Response, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin from Vercel frontend

# Load env
try:
    with open(os.path.join(os.path.dirname(__file__), '.env')) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                os.environ.setdefault(key, val)
except FileNotFoundError:
    pass

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

_active_research = {}


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'research-server'})


@app.route('/api/research/stream', methods=['POST', 'OPTIONS'])
def research_stream():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json(force=True)
    query = data.get('query', '').strip()
    session_id = data.get('session_id', str(uuid.uuid4()))

    if not query:
        return jsonify({'error': 'query is required'}), 400

    if session_id in _active_research:
        return jsonify({'error': 'Research already in progress'}), 429
    _active_research[session_id] = True

    event_queue = queue.Queue()

    def emit_callback(event_type, event_data):
        event_queue.put((event_type, event_data))

    def run_research():
        try:
            from agent_committee import research
            result = research(query, emit=emit_callback)
            if not result.get('error') and not result.get('final_report'):
                event_queue.put(('error', {'message': 'Pipeline completed without producing a report'}))
        except Exception as e:
            event_queue.put(('error', {'message': str(e), 'traceback': traceback.format_exc()}))
        finally:
            event_queue.put(('__done__', None))
            _active_research.pop(session_id, None)

    thread = threading.Thread(target=run_research, daemon=True)
    thread.start()

    def generate():
        import urllib.request
        final_data = None
        while True:
            try:
                event_type, event_data = event_queue.get(timeout=600)  # 10 min timeout
            except queue.Empty:
                yield f"event: error\ndata: {json.dumps({'message': 'Timeout (10 min)'})}\n\n"
                break

            if event_type == '__done__':
                # Save report to Supabase
                if final_data and SUPABASE_KEY:
                    try:
                        report_row = {
                            'id': str(uuid.uuid4()),
                            'query': query,
                            'report': final_data.get('report', ''),
                            'risk_flags': final_data.get('risk_flags', ''),
                            'tickers': final_data.get('tickers', []),
                            'intents': final_data.get('intents', []),
                            'sources': final_data.get('sources', []),
                            'created_at': datetime.now(timezone.utc).isoformat(),
                        }
                        req_body = json.dumps(report_row).encode()
                        req = urllib.request.Request(
                            f'{SUPABASE_URL}/rest/v1/research_reports',
                            data=req_body,
                            headers={
                                'apikey': SUPABASE_KEY,
                                'Authorization': f'Bearer {SUPABASE_KEY}',
                                'Content-Type': 'application/json',
                                'Prefer': 'return=representation',
                            },
                            method='POST'
                        )
                        urllib.request.urlopen(req, timeout=10)
                    except Exception:
                        pass
                break

            if event_type == 'complete':
                final_data = event_data

            if isinstance(event_data, dict):
                event_data['_session_id'] = session_id
            yield f"event: {event_type}\ndata: {json.dumps(event_data, default=str)}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/reports')
def list_reports():
    if not SUPABASE_KEY:
        return jsonify([])
    try:
        import urllib.request
        url = f'{SUPABASE_URL}/rest/v1/research_reports?select=id,query,tickers,created_at&order=created_at.desc&limit=50'
        req = urllib.request.Request(url, headers={
            'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'
        })
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<report_id>')
def get_report(report_id):
    if not SUPABASE_KEY:
        return jsonify({'error': 'No Supabase key'}), 500
    try:
        import urllib.request
        url = f'{SUPABASE_URL}/rest/v1/research_reports?id=eq.{report_id}'
        req = urllib.request.Request(url, headers={
            'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'
        })
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return jsonify(data[0] if data else {'error': 'Not found'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<report_id>', methods=['DELETE'])
def delete_report(report_id):
    if not SUPABASE_KEY:
        return jsonify({'error': 'No Supabase key'}), 500
    try:
        import urllib.request
        url = f'{SUPABASE_URL}/rest/v1/research_reports?id=eq.{report_id}'
        req = urllib.request.Request(url, headers={
            'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
        }, method='DELETE')
        urllib.request.urlopen(req, timeout=10)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5050)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()
    print(f"🔬 Research Server running on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True, debug=False)
