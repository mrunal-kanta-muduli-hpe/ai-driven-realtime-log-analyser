#!/usr/bin/env python3
"""
Real-time Dashboard Server for AI Driven Realtime Log Analyser
Provides live dashboard updates with WebSocket support
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading
import websockets
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import webbrowser

logger = logging.getLogger(__name__)


class RealtimeDashboardServer:
    """
    Enhanced HTTP/WebSocket server for real-time dashboard updates
    """
    
    def __init__(self, analyzer, port: int = 8889, websocket_port: int = 8890):
        self.analyzer = analyzer
        self.port = port
        self.websocket_port = websocket_port
        self.connected_clients = set()
        self.is_running = False
        self.last_update = time.time()
        self.update_interval = 2.0  # Update every 2 seconds
        
    async def start_server(self):
        """Start both HTTP and WebSocket servers"""
        self.is_running = True
        
        # Start HTTP server in background thread (non-daemon)
        http_thread = threading.Thread(target=self._start_http_server, daemon=False)
        http_thread.start()
        
        # Give HTTP server time to start
        await asyncio.sleep(1)
        
        # Start WebSocket server
        logger.info(f"🔌 Starting WebSocket server on port {self.websocket_port}")
        
        # Start periodic update task
        update_task = asyncio.create_task(self._periodic_updates())
        
        # Start WebSocket server
        async with websockets.serve(self._websocket_handler, "localhost", self.websocket_port):
            logger.info(f"✅ Real-time dashboard server started")
            logger.info(f"🌐 Dashboard: http://localhost:{self.port}/realtime_dashboard.html")
            logger.info(f"🔌 WebSocket: ws://localhost:{self.websocket_port}")
            
            # Open browser automatically
            webbrowser.open(f"http://localhost:{self.port}/realtime_dashboard.html")
            
            # Keep server running
            await update_task
    
    def _start_http_server(self):
        """Start HTTP server for serving dashboard files"""
        analyzer = self.analyzer  # Store reference for inner class
        
        class RealTimeHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                # Set directory to project root to access templates
                project_root = Path(__file__).parent.parent.parent
                super().__init__(*args, directory=str(project_root), **kwargs)
            
            def log_message(self, format, *args):
                """Override to use our logger"""
                logger.info(f"HTTP: {format % args}")
            
            def end_headers(self):
                # Add CORS headers for WebSocket connection
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                super().end_headers()
            
            def do_GET(self):
                # Handle special routes - strip query parameters
                path = self.path.split('?')[0]  # Remove query parameters
                logger.info(f"🌐 HTTP GET request for: {path}")
                
                if path == '/realtime_dashboard.html':
                    self._serve_dashboard()
                elif path == '/health':
                    self._serve_health()
                elif path.startswith('/api/'):
                    self._handle_api_request()
                else:
                    logger.info(f"🌐 Serving static file: {path}")
                    super().do_GET()
            
            def _serve_health(self):
                """Serve a simple health check"""
                try:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"Real-time dashboard server is running!")
                    logger.info("✅ Health check served")
                except Exception as e:
                    logger.error(f"❌ Error serving health check: {e}")
            
            def _serve_dashboard(self):
                """Serve the real-time dashboard HTML"""
                dashboard_path = Path(__file__).parent / 'templates' / 'realtime_dashboard.html'
                
                logger.info(f"Attempting to serve dashboard from: {dashboard_path}")
                logger.info(f"File exists: {dashboard_path.exists()}")
                
                try:
                    with open(dashboard_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                    logger.info("✅ Dashboard served successfully")
                    
                except FileNotFoundError:
                    logger.error(f"❌ Dashboard template not found: {dashboard_path}")
                    self.send_error(404, f"Dashboard template not found: {dashboard_path}")
                except Exception as e:
                    logger.error(f"❌ Error serving dashboard: {e}")
                    self.send_error(500, f"Error serving dashboard: {e}")
            
            def _handle_api_request(self):
                """Handle REST API requests for real-time data"""
                if self.path == '/api/stats':
                    # Return current statistics
                    stats = {
                        'total_entries': len(analyzer.processed_entries) if hasattr(analyzer, 'processed_entries') else 0,
                        'error_count': len([e for e in analyzer.processed_entries if e.level == 'ERROR']) if hasattr(analyzer, 'processed_entries') else 0,
                        'warning_count': len([e for e in analyzer.processed_entries if e.level == 'WARNING']) if hasattr(analyzer, 'processed_entries') else 0,
                        'components': len(set(e.component for e in analyzer.processed_entries)) if hasattr(analyzer, 'processed_entries') else 0,
                        'last_update': datetime.now().isoformat(),
                        'is_monitoring': getattr(analyzer, 'is_monitoring', False)
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(stats).encode())
                
                elif self.path == '/api/recent':
                    # Return recent log entries
                    recent_entries = analyzer.processed_entries[-10:] if hasattr(analyzer, 'processed_entries') else []
                    entries_data = [
                        {
                            'timestamp': entry.timestamp.isoformat() if hasattr(entry, 'timestamp') and entry.timestamp else datetime.now().isoformat(),
                            'level': getattr(entry, 'level', 'INFO'),
                            'component': getattr(entry, 'component', 'Unknown'),
                            'message': (entry.message[:100] + '...' if len(entry.message) > 100 else entry.message) if hasattr(entry, 'message') else 'No message'
                        }
                        for entry in recent_entries
                    ]
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(entries_data).encode())
                
                else:
                    self.send_response(404)
                    self.end_headers()
        
        try:
            # Try binding to localhost first, then fallback to all interfaces
            try:
                httpd = socketserver.TCPServer(("localhost", self.port), RealTimeHTTPHandler)
                server_host = "localhost"
            except OSError:
                httpd = socketserver.TCPServer(("127.0.0.1", self.port), RealTimeHTTPHandler)
                server_host = "127.0.0.1"
            
            logger.info(f"🌐 HTTP server started on {server_host}:{self.port}")
            httpd.serve_forever()
            
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.error(f"❌ Port {self.port} is already in use")
            else:
                logger.error(f"❌ Failed to bind HTTP server to port {self.port}: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to start HTTP server: {e}")
        finally:
            logger.info(f"🛑 HTTP server on port {self.port} stopped")
    
    async def _websocket_handler(self, websocket):
        """Handle WebSocket connections"""
        logger.info(f"🔌 New WebSocket client connected from {websocket.remote_address}")
        self.connected_clients.add(websocket)
        
        try:
            # Send initial data
            await self._send_initial_data(websocket)
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(websocket, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket client disconnected")
        
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        
        finally:
            self.connected_clients.discard(websocket)
    
    async def _send_initial_data(self, websocket):
        """Send initial dashboard data to new client"""
        try:
            # Load current analysis results
            results_file = self.analyzer.config.get_output_path() / "analysis_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    analysis_data = json.load(f)
                
                # Transform data to match dashboard expectations
                dashboard_data = self._transform_analysis_data(analysis_data)
            else:
                dashboard_data = {
                    "stats": {
                        "total_entries": 0,
                        "error_count": 0,
                        "warning_count": 0,
                        "anomalies": 0,
                        "patterns": 0,
                        "ml_accuracy": 0.0
                    },
                    "recent_logs": []
                }
            
            # Send initial data
            initial_message = {
                "type": "initial_data",
                "stats": dashboard_data["stats"],
                "recent_logs": dashboard_data.get("recent_logs", []),
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(initial_message))
            logger.info("📤 Sent initial data to WebSocket client")
            
        except Exception as e:
            logger.error(f"❌ Failed to send initial data: {e}")
    
    def _transform_analysis_data(self, analysis_data):
        """Transform analysis data to dashboard format"""
        try:
            summary = analysis_data.get("summary", {})
            anomalies_data = analysis_data.get("anomalies", {})
            patterns = analysis_data.get("error_patterns", {})
            ml_data = analysis_data.get("ml_analysis", {})
            
            # Calculate anomalies from error patterns and summary
            total_anomalies = summary.get("error_count", 0)
            if hasattr(self.analyzer, 'detected_anomalies'):
                total_anomalies = len(self.analyzer.detected_anomalies)
            elif isinstance(anomalies_data, list):
                total_anomalies = len(anomalies_data)
            elif isinstance(anomalies_data, dict) and "total_anomalies" in anomalies_data:
                total_anomalies = anomalies_data["total_anomalies"]
            
            # Map to dashboard format
            stats = {
                "total_entries": summary.get("total_entries", 0),
                "error_count": summary.get("error_count", 0),
                "warning_count": summary.get("warning_count", 0),
                "anomalies": total_anomalies,
                "patterns": len(patterns) if isinstance(patterns, dict) else 0,
                "ml_accuracy": ml_data.get("accuracy", 1.0) if ml_data else 1.0
            }
            
            # Get recent logs from timeline or create from error patterns
            recent_logs = []
            timeline = analysis_data.get("timeline", [])
            
            # Add recent logs from error patterns
            if isinstance(patterns, dict):
                for pattern, count in list(patterns.items())[:5]:
                    recent_logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "level": "ERROR",
                        "component": "DSC",
                        "message": pattern[:80] + "..." if len(pattern) > 80 else pattern
                    })
            
            # Add timeline-based logs if available
            if timeline and len(timeline) > 0:
                for entry in timeline[-3:]:  # Last 3 timeline entries
                    if entry.get("error", 0) > 0:
                        recent_logs.append({
                            "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                            "level": "ERROR",
                            "component": "System",
                            "message": f"Detected {entry.get('error')} errors at {entry.get('timestamp', 'unknown time')}"
                        })
            
            return {
                "stats": stats,
                "recent_logs": recent_logs[-8:]  # Keep last 8 logs for compact view
            }
            
        except Exception as e:
            logger.error(f"❌ Error transforming analysis data: {e}")
            return {
                "stats": {
                    "total_entries": 0,
                    "error_count": 0,
                    "warning_count": 0,
                    "anomalies": 0,
                    "patterns": 0,
                    "ml_accuracy": 0.0
                },
                "recent_logs": []
            }
    
    async def _handle_websocket_message(self, websocket, data):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        if message_type == "request_update":
            # Client requesting immediate update
            await self._send_live_update(websocket)
        
        elif message_type == "subscribe":
            # Client subscribing to specific data types
            logger.info(f"📡 Client subscribed to: {data.get('channels', [])}")
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def _periodic_updates(self):
        """Periodically send updates to connected clients"""
        while self.is_running:
            try:
                if self.connected_clients and self.analyzer.is_monitoring:
                    # Check if we have new data
                    current_time = time.time()
                    if current_time - self.last_update >= self.update_interval:
                        await self._broadcast_updates()
                        self.last_update = current_time
                
                await asyncio.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"❌ Error in periodic updates: {e}")
                await asyncio.sleep(5.0)
    
    async def _broadcast_updates(self):
        """Broadcast updates to all connected clients"""
        if not self.connected_clients:
            return
        
        try:
            # Load latest analysis results
            results_file = self.analyzer.config.get_output_path() / "analysis_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    analysis_data = json.load(f)
                dashboard_data = self._transform_analysis_data(analysis_data)
            else:
                # Generate current stats from analyzer
                dashboard_data = {
                    "stats": {
                        "total_entries": len(self.analyzer.processed_entries),
                        "error_count": len([e for e in self.analyzer.processed_entries if e.level == 'ERROR']),
                        "warning_count": len([e for e in self.analyzer.processed_entries if e.level == 'WARNING']),
                        "anomalies": len(getattr(self.analyzer, 'detected_anomalies', [])),
                        "patterns": len(getattr(self.analyzer, 'error_patterns', {})),
                        "ml_accuracy": 1.0
                    },
                    "recent_logs": []
                }
            
            # Prepare update message
            update_data = {
                "type": "live_update",
                "timestamp": datetime.now().isoformat(),
                "stats": dashboard_data["stats"],
                "recent_logs": dashboard_data.get("recent_logs", [])
            }
            
            # Add recent entries from analyzer if no recent_logs
            if not update_data["recent_logs"] and hasattr(self.analyzer, 'processed_entries'):
                recent_entries = self.analyzer.processed_entries[-5:]  # Last 5 entries
                update_data["recent_logs"] = [
                    {
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else datetime.now().isoformat(),
                        "level": entry.level,
                        "component": entry.component or "System",
                        "message": entry.message[:100] + '...' if len(entry.message) > 100 else entry.message
                    }
                    for entry in recent_entries
                ]
            
            # Broadcast to all clients
            message = json.dumps(update_data)
            disconnected_clients = set()
            
            for client in self.connected_clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.error(f"❌ Failed to send update to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.connected_clients -= disconnected_clients
            
            if self.connected_clients:
                logger.info(f"📡 Broadcasted updates to {len(self.connected_clients)} clients")
            
        except Exception as e:
            logger.error(f"❌ Failed to broadcast updates: {e}")
    
    async def _send_live_update(self, websocket):
        """Send immediate update to specific client"""
        try:
            # Load latest analysis results
            results_file = self.analyzer.config.get_output_path() / "analysis_results.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    analysis_data = json.load(f)
                dashboard_data = self._transform_analysis_data(analysis_data)
            else:
                dashboard_data = {
                    "stats": {
                        "total_entries": 0,
                        "error_count": 0,
                        "warning_count": 0,
                        "anomalies": 0,
                        "patterns": 0,
                        "ml_accuracy": 0.0
                    },
                    "recent_logs": []
                }
            
            update_message = {
                "type": "live_update",
                "stats": dashboard_data["stats"],
                "recent_logs": dashboard_data.get("recent_logs", []),
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(update_message))
            
        except Exception as e:
            logger.error(f"❌ Failed to send live update: {e}")
    
    def stop_server(self):
        """Stop the real-time server"""
        self.is_running = False
        logger.info("🛑 Real-time dashboard server stopped")


async def start_realtime_dashboard(analyzer, port: int = 8889):
    """
    Start real-time dashboard server
    
    Args:
        analyzer: SmartLogAnalyzer instance
        port: HTTP server port
    """
    server = RealtimeDashboardServer(analyzer, port)
    await server.start_server()
