#!/usr/bin/env python3
"""
Dashboard server for AI Driven Realtime Log Analyser
Serves generated visualizations via HTTP
"""

import http.server
import socketserver
import webbrowser
import sys
import logging
from pathlib import Path
import argparse
from utils.port_finder import find_available_port

logger = logging.getLogger(__name__)


class DashboardServer:
    """HTTP server for serving dashboards and visualizations"""
    
    def __init__(self, directory: str = ".", port: int = 8000, auto_port: bool = True):
        self.directory = Path(directory).resolve()
        self.requested_port = port
        self.auto_port = auto_port
        self.actual_port = None
        
    def serve(self):
        """Start the HTTP server with automatic port selection"""
        if not self.directory.exists():
            logger.error(f"❌ Directory {self.directory} does not exist")
            return
        
        # Find available port
        if self.auto_port:
            try:
                self.actual_port = find_available_port(self.requested_port)
                if self.actual_port != self.requested_port:
                    logger.info(f"⚠️  Port {self.requested_port} was busy, using port {self.actual_port}")
            except RuntimeError as e:
                logger.error(f"❌ {e}")
                return
        else:
            self.actual_port = self.requested_port
        
        try:
            import os
            original_dir = Path.cwd()
            os.chdir(self.directory)
            
            logger.info(f"🌐 Starting HTTP server...")
            logger.info(f"📁 Serving directory: {self.directory}")
            logger.info(f"🔗 Server URL: http://localhost:{self.actual_port}")
            
            # Create server
            Handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", self.actual_port), Handler) as httpd:
                logger.info(f"✅ Server started on port {self.actual_port}")
                
                # Look for dashboard files
                dashboard_files = list(self.directory.glob("**/interactive_dashboard.html"))
                if dashboard_files:
                    logger.info(f"\\n📊 Available dashboards:")
                    for i, dashboard in enumerate(dashboard_files, 1):
                        rel_path = dashboard.relative_to(self.directory)
                        logger.info(f"  {i}. {rel_path}")
                        logger.info(f"     🔗 http://localhost:{self.actual_port}/{rel_path}")
                    
                    # Open the first dashboard
                    first_dashboard = dashboard_files[0].relative_to(self.directory)
                    url = f"http://localhost:{self.actual_port}/{first_dashboard}"
                    logger.info(f"\\n🚀 Opening dashboard: {url}")
                    webbrowser.open(url)
                else:
                    # Look for any HTML files
                    html_files = list(self.directory.glob("**/*.html"))
                    if html_files:
                        logger.info(f"\\n📄 Available HTML files:")
                        for html_file in html_files[:5]:  # Show first 5
                            rel_path = html_file.relative_to(self.directory)
                            logger.info(f"  🔗 http://localhost:{self.actual_port}/{rel_path}")
                        
                        # Open the first HTML file
                        first_html = html_files[0].relative_to(self.directory)
                        url = f"http://localhost:{self.actual_port}/{first_html}"
                        webbrowser.open(url)
                    else:
                        logger.info("\\n📂 No dashboard files found. Serving directory listing.")
                        url = f"http://localhost:{self.actual_port}"
                        webbrowser.open(url)
                
                logger.info(f"\\n⏹️  Press Ctrl+C to stop the server")
                httpd.serve_forever()
                
        except KeyboardInterrupt:
            logger.info(f"\\n⏹️  Server stopped")
        except Exception as e:
            logger.error(f"❌ Error starting server: {e}")
        finally:
            os.chdir(original_dir)


def main():
    """Main entry point for dashboard server"""
    parser = argparse.ArgumentParser(
        description="Serve Smart Log Analyzer visualizations via HTTP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Serve current directory on default port 8000
  python dashboard_server.py

  # Serve specific visualization directory
  python dashboard_server.py --dir output

  # Use custom port
  python dashboard_server.py --port 8080
        """
    )
    
    parser.add_argument(
        "-d", "--dir",
        default=".",
        help="Directory to serve (default: current directory)"
    )
    
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to serve on (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    server = DashboardServer(args.dir, args.port)
    server.serve()


if __name__ == "__main__":
    main()
