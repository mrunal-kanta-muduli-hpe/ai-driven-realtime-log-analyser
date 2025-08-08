#!/usr/bin/env python3
"""
Port finder utility for AI Driven Realtime Log Analyser
Finds available ports with retry logic
"""

import socket
import logging

logger = logging.getLogger(__name__)


def find_available_port(start_port: int = 8000, max_attempts: int = 50) -> int:
    """
    Find an available port starting from start_port
    
    Args:
        start_port: Starting port number to check
        max_attempts: Maximum number of ports to try
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available port is found
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                logger.debug(f"Port {port} is available")
                return port
        except OSError:
            logger.debug(f"Port {port} is busy")
            continue
    
    raise RuntimeError(f"Could not find available port in range {start_port}-{start_port + max_attempts}")


def find_available_ports(start_ports: list, max_attempts: int = 50) -> list:
    """
    Find multiple available ports
    
    Args:
        start_ports: List of preferred starting ports
        max_attempts: Maximum number of ports to try for each
        
    Returns:
        List of available ports (same length as start_ports)
    """
    available_ports = []
    used_ports = set()
    
    for start_port in start_ports:
        port = start_port
        attempts = 0
        
        while attempts < max_attempts:
            if port not in used_ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('localhost', port))
                        available_ports.append(port)
                        used_ports.add(port)
                        logger.debug(f"Port {port} assigned (requested {start_port})")
                        break
                except OSError:
                    pass
            
            port += 1
            attempts += 1
        else:
            raise RuntimeError(f"Could not find available port starting from {start_port}")
    
    return available_ports


def is_port_available(port: int) -> bool:
    """
    Check if a specific port is available
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False
