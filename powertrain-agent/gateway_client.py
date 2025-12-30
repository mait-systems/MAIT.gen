#!/usr/bin/env python3
"""
Gateway Client for MAIT PowertrainAgent
Handles communication with the proprietary MAIT Prompt Gateway
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import math
import pandas as pd

class GatewayClient:
    """
    Pure HTTP client for communicating with MAIT Prompt Gateway
    Handles gateway analysis requests and connection validation
    """
    
    def __init__(self, config: dict):
        """Initialize gateway client"""
        self.config = config
        self.logger = logging.getLogger('GatewayClient')
        
        # Gateway configuration
        self.gateway_url = config.get('gateway_url', 'http://localhost:8000')
        self.api_key = config.get('gateway_api_key', 'dev-key-123')
        self.timeout = config.get('gateway_timeout', 30)
        
        # Customer InfluxDB config for gateway
        self.influx_config = config.get('influxdb', {})
        
        # Generator configuration
        self.rated_power_kw = config.get('generator', {}).get('rated_power_kw', 150)
        
        # Connection state tracking
        self.last_successful_connection = None
        self.connection_failures = 0
        
        self.logger.info(f"Gateway client initialized - URL: {self.gateway_url}")
        self.logger.info(f"Generator rated power: {self.rated_power_kw} kW")
    
    def _sanitize_for_json(self, obj):
        """Recursively sanitize any object for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return 0
            return obj
        elif obj is None:
            return None
        else:
            # For any pandas-specific types, convert to basic Python types
            try:
                if pd.isna(obj):
                    return None
            except (TypeError, ValueError):
                pass
            
            # Convert numpy/pandas types to basic Python types
            if hasattr(obj, 'item'):  # numpy scalars
                try:
                    return self._sanitize_for_json(obj.item())
                except (ValueError, AttributeError):
                    pass
            
            return obj
    
    def analyze(self, metrics: Dict[str, Any], site_id: str = "default", ai_enabled: bool = True) -> Dict[str, Any]:
        """
        Send metrics to gateway for AI analysis
        
        Args:
            metrics: Current generator metrics
            site_id: Customer site identifier
            ai_enabled: Whether AI analysis should be performed (prevents OpenAI API calls if False)
            
        Returns:
            Gateway analysis result
        
        Raises:
            Exception: When gateway is unreachable or returns errors
        """
        try:
            self.logger.info(f"Sending analysis request to gateway for site: {site_id}")
            
            # Sanitize metrics to ensure JSON compliance (fix NaN/infinity values)
            sanitized_metrics = self._sanitize_for_json(metrics)
            sanitized_influx_config = self._sanitize_for_json(self.influx_config)
            
            # Prepare request payload
            payload = {
                "site_id": site_id,
                "metrics": sanitized_metrics,
                "influx_config": sanitized_influx_config,
                "ai_enabled": ai_enabled
            }
            
            # Headers with authentication
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Make request to gateway
            response = requests.post(
                f"{self.gateway_url}/api/analyze",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # Track successful connection
                self.last_successful_connection = datetime.now()
                self.connection_failures = 0
                result['connection_status'] = 'ONLINE'
                result['last_successful_connection'] = self.last_successful_connection.isoformat()
                self.logger.info("Gateway analysis completed successfully")
                return result
            else:
                self.logger.error(f"Gateway request failed: {response.status_code} - {response.text}")
                self.connection_failures += 1
                raise Exception(f"Gateway error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.logger.warning("Gateway request timed out")
            self.connection_failures += 1
            raise requests.exceptions.Timeout("Gateway timeout")
            
        except requests.exceptions.ConnectionError:
            self.logger.warning("Cannot connect to gateway")
            self.connection_failures += 1
            raise requests.exceptions.ConnectionError("Gateway unreachable")
            
        except Exception as e:
            self.logger.error(f"Gateway request failed: {str(e)}")
            self.connection_failures += 1
            raise Exception(f"Gateway error: {str(e)}")
    
    
    def validate_connection(self) -> bool:
        """Test connection to gateway and customer InfluxDB"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.gateway_url}/api/validate-connection",
                json=self.influx_config,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"Gateway connection validated: {result.get('message', 'OK')}")
                return True
            else:
                self.logger.error(f"Gateway validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Gateway validation error: {str(e)}")
            return False
    
