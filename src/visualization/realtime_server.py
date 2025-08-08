#!/usr/bin/env python3
"""
Real-time Dashboard Server for AI Driven Realtime Log Analyser
Provides live dashboard updates with WebSocket support
"""

import asyncio
import json
import logging
import time
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import threading
import websockets
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import webbrowser

# Use absolute import instead of relative
try:
    from utils.port_finder import find_available_port, find_available_ports
except ImportError:
    # Fallback port finder if import fails
    def find_available_port(start_port: int = 8000, max_attempts: int = 50) -> int:
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")
    
    def find_available_ports(start_ports: list, max_attempts: int = 50) -> list:
        result = []
        used_ports = set()
        for start_port in start_ports:
            for port in range(start_port, start_port + max_attempts):
                if port not in used_ports:
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.bind(('localhost', port))
                            result.append(port)
                            used_ports.add(port)
                            break
                    except OSError:
                        continue
            else:
                raise RuntimeError(f"Could not find available port starting from {start_port}")
        return result

logger = logging.getLogger(__name__)


class RealtimeDashboardServer:
    """
    Enhanced HTTP/WebSocket server for real-time dashboard updates with automatic port selection
    """
    
    def __init__(self, analyzer, port: int = 8889, websocket_port: int = 8890, auto_port: bool = True):
        self.analyzer = analyzer
        self.requested_port = port
        self.requested_websocket_port = websocket_port
        self.auto_port = auto_port
        self.actual_port = None
        self.actual_websocket_port = None
        self.connected_clients = set()
        self.is_running = False
        self.last_update = time.time()
        self.update_interval = 2.0  # Update every 2 seconds
        
    async def start_server(self):
        """Start both HTTP and WebSocket servers with automatic port selection"""
        self.is_running = True
        
        # Find available ports
        if self.auto_port:
            try:
                ports = find_available_ports([self.requested_port, self.requested_websocket_port])
                self.actual_port = ports[0]
                self.actual_websocket_port = ports[1]
                
                if self.actual_port != self.requested_port:
                    logger.info(f"⚠️  HTTP port {self.requested_port} was busy, using port {self.actual_port}")
                if self.actual_websocket_port != self.requested_websocket_port:
                    logger.info(f"⚠️  WebSocket port {self.requested_websocket_port} was busy, using port {self.actual_websocket_port}")
                    
            except RuntimeError as e:
                logger.error(f"❌ {e}")
                return
        else:
            self.actual_port = self.requested_port
            self.actual_websocket_port = self.requested_websocket_port
        
        # Start HTTP server in background thread (non-daemon)
        http_thread = threading.Thread(target=self._start_http_server, daemon=False)
        http_thread.start()
        
        # Give HTTP server time to start
        await asyncio.sleep(1)
        
        # Start WebSocket server
        logger.info(f"🔌 Starting WebSocket server on port {self.actual_websocket_port}")
        
        # Start periodic update task
        update_task = asyncio.create_task(self._periodic_updates())
        
        # Start WebSocket server
        async with websockets.serve(self._websocket_handler, "localhost", self.actual_websocket_port):
            logger.info(f"✅ Real-time dashboard server started")
            logger.info(f"🌐 Dashboard: http://localhost:{self.actual_port}/realtime_dashboard.html")
            logger.info(f"🔌 WebSocket: ws://localhost:{self.actual_websocket_port}")
            
            # Open browser automatically
            webbrowser.open(f"http://localhost:{self.actual_port}/realtime_dashboard.html")
            
            # Keep server running
            await update_task
    
    def _start_http_server(self):
        """Start HTTP server for serving dashboard files with retry logic"""
        analyzer = self.analyzer  # Store reference for inner class
        actual_port = self.actual_port
        actual_websocket_port = self.actual_websocket_port
        
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
                    
                    # Replace WebSocket port placeholder with actual port
                    content = content.replace('ws://localhost:8890', f'ws://localhost:{actual_websocket_port}')
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                    logger.info("✅ Dashboard served successfully")
                    
                except FileNotFoundError:
                    logger.error(f"❌ Dashboard template not found: {dashboard_path}")
                    self.send_error(404, f"Dashboard template not found")
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
            with socketserver.TCPServer(("", actual_port), RealTimeHTTPHandler) as httpd:
                logger.info(f"🌐 HTTP server started on port {actual_port}")
                httpd.serve_forever()
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.error(f"❌ Port {actual_port} is already in use")
            else:
                logger.error(f"❌ HTTP server error: {e}")
            logger.info(f"🛑 HTTP server on port {actual_port} stopped")
    
    async def _websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.connected_clients.add(websocket)
        logger.info(f"🔌 WebSocket client connected. Total clients: {len(self.connected_clients)}")
        
        try:
            # Send initial data
            await self._send_update(websocket)
            
            # Keep connection alive and handle messages
            async for message in websocket:
                logger.info(f"📨 Received WebSocket message: {message}")
                # Handle client messages if needed
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket client disconnected")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🔌 Client removed. Total clients: {len(self.connected_clients)}")
    
    async def _send_update(self, websocket):
        """Send update to a specific WebSocket client"""
        try:
            # Prepare update data
            update_data = {
                'timestamp': datetime.now().isoformat(),
                'stats': self._get_current_stats(),
                'recent_entries': self._get_recent_entries(),
                'status': 'connected'
            }
            
            await websocket.send(json.dumps(update_data))
            logger.debug("📡 Update sent to WebSocket client")
            
        except Exception as e:
            logger.error(f"❌ Error sending WebSocket update: {e}")
    
    async def _broadcast_update(self):
        """Broadcast update to all connected WebSocket clients"""
        if not self.connected_clients:
            return
        
        # Prepare update data
        update_data = {
            'timestamp': datetime.now().isoformat(),
            'stats': self._get_current_stats(),
            'recent_entries': self._get_recent_entries(),
            'status': 'update'
        }
        
        # Send to all clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(update_data))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"❌ Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
        
        if disconnected_clients:
            logger.info(f"🔌 Removed {len(disconnected_clients)} disconnected clients")
    
    async def _periodic_updates(self):
        """Send periodic updates to connected clients"""
        while self.is_running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._broadcast_update()
            except Exception as e:
                logger.error(f"❌ Error in periodic update: {e}")
    
    def _get_current_stats(self):
        """Get current analysis statistics"""
        if not hasattr(self.analyzer, 'processed_entries'):
            return {
                'total_entries': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'components': 0,
                'last_update': datetime.now().isoformat()
            }
        
        entries = self.analyzer.processed_entries
        return {
            'total_entries': len(entries),
            'error_count': len([e for e in entries if e.level == 'ERROR']),
            'warning_count': len([e for e in entries if e.level == 'WARNING']),
            'info_count': len([e for e in entries if e.level == 'INFO']),
            'components': len(set(e.component for e in entries)),
            'last_update': datetime.now().isoformat()
        }
    
    def _get_recent_entries(self):
        """Get recent log entries"""
        if not hasattr(self.analyzer, 'processed_entries'):
            return []
        
        recent_entries = self.analyzer.processed_entries[-10:]
        return [
            {
                'timestamp': entry.timestamp.isoformat() if hasattr(entry, 'timestamp') and entry.timestamp else datetime.now().isoformat(),
                'level': getattr(entry, 'level', 'INFO'),
                'component': getattr(entry, 'component', 'Unknown'),
                'message': (entry.message[:100] + '...' if len(entry.message) > 100 else entry.message) if hasattr(entry, 'message') else 'No message'
            }
            for entry in recent_entries
        ]
    
    def stop(self):
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
