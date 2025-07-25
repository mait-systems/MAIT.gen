#!/usr/bin/env python3
"""
PowertrainAgent - Real-time and trend-based monitoring agent for diesel generator powertrain health
Version 1.0 - Initial implementation with persistent memory system

This agent analyzes both live telemetry and historical data summaries, detects anomalies,
and provides interpreted insight via AI (LLM-based) analysis with cumulative memory.
"""

import os
import sys
import time
import logging
import yaml
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from influx_query import InfluxQueryManager
from memory_manager import PowertrainMemoryManager
from prompt_builder import MemoryEnhancedPromptBuilder
from logger import PowertrainLogger

@dataclass
class PowertrainMetrics:
    """Current powertrain metrics snapshot"""
    timestamp: datetime
    engine_speed: float
    engine_run_speed: float
    engine_oil_pressure: float
    generator_total_real_power: float
    engine_coolant_temperature: float
    load_band: str
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'engine_speed': self.engine_speed,
            'engine_run_speed': self.engine_run_speed,
            'engine_oil_pressure': self.engine_oil_pressure,
            'generator_total_real_power': self.generator_total_real_power,
            'engine_coolant_temperature': self.engine_coolant_temperature,
            'load_band': self.load_band
        }

class PowertrainAgent:
    """
    Main PowertrainAgent class that orchestrates the monitoring and analysis process
    """
    
    def __init__(self, config_path: str = "generator_config.yaml"):
        """Initialize the PowertrainAgent with configuration"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize managers
        self.influx_manager = InfluxQueryManager(self.config)
        self.memory_manager = PowertrainMemoryManager(self.config)
        self.prompt_builder = MemoryEnhancedPromptBuilder(self.config)
        self.result_logger = PowertrainLogger(self.config)
        
        self.logger.info("PowertrainAgent initialized successfully")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging_config = self.config.get('logging', {})
        log_level = getattr(logging, logging_config.get('level', 'INFO'))
        
        logger = logging.getLogger('PowertrainAgent')
        logger.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # File handler
        log_filename = logging_config.get('filename', 'powertrain_agent.log')
        file_handler = logging.FileHandler(f"/app/logs/{log_filename}")
        file_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            logging_config.get('format', '%(asctime)s [%(levelname)s] %(message)s'),
            datefmt=logging_config.get('datefmt', '%H:%M:%S')
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def get_load_band(self, power_percentage: float) -> str:
        """Classify current load into bands for historical comparison"""
        if power_percentage < 0:
            return "0%"
        elif power_percentage < 20:
            return "0-20%"
        elif power_percentage < 40:
            return "20-40%"
        elif power_percentage < 60:
            return "40-60%"
        elif power_percentage < 80:
            return "60-80%"
        else:
            return "80-100%"
    
    def collect_live_metrics(self) -> Optional[PowertrainMetrics]:
        """Collect current powertrain metrics from InfluxDB"""
        try:
            live_data = self.influx_manager.get_latest_powertrain_data()
            
            if not live_data:
                self.logger.warning("No live data available")
                return None
            
            load_band = self.get_load_band(live_data.get('Generator_Total_Real_Power', 0))
            
            metrics = PowertrainMetrics(
                timestamp=datetime.now(),
                engine_speed=live_data.get('Engine_Speed', 0),
                engine_run_speed=live_data.get('Engine_Run_Speed', 0),
                engine_oil_pressure=live_data.get('Engine_Oil_Pressure', 0),
                generator_total_real_power=live_data.get('Generator_Total_Real_Power', 0),
                engine_coolant_temperature=live_data.get('Engine_Coolant_Temperature', 0),
                load_band=load_band
            )
            
            self.logger.info(f"Collected live metrics: Load={load_band}, "
                           f"RPM={metrics.engine_speed}, Oil={metrics.engine_oil_pressure}kPa")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect live metrics: {e}")
            return None
    
    def analyze_powertrain_health(self, current_metrics: PowertrainMetrics) -> Dict[str, Any]:
        """
        Main analysis function that combines live data with historical memory
        """
        try:
            self.logger.info(f"Starting powertrain health analysis for load band: {current_metrics.load_band}")
            
            # Step 1: Update memory with new data (incremental)
            self.memory_manager.update_memory_incremental(current_metrics)
            
            # Step 2: Retrieve relevant historical context
            memory_context = self.memory_manager.get_analysis_context(current_metrics)
            
            # Step 3: Build memory-enhanced prompt
            analysis_prompt = self.prompt_builder.build_analysis_prompt(
                current_metrics, memory_context
            )
            
            # Step 4: Get AI analysis
            ai_analysis = self.prompt_builder.get_ai_analysis(analysis_prompt)
            
            # Step 5: Process and store results
            analysis_result = {
                'timestamp': current_metrics.timestamp.isoformat(),
                'current_metrics': current_metrics.to_dict(),
                'memory_context': memory_context,
                'ai_analysis': ai_analysis,
                'alert_level': self._extract_alert_level(ai_analysis),
                'recommendations': self._extract_recommendations(ai_analysis)
            }
            
            # Step 6: Store analysis results and update AI memory
            self.result_logger.store_analysis_result(analysis_result)
            self.memory_manager.update_ai_memory(analysis_result)
            
            self.logger.info(f"Analysis completed with alert level: {analysis_result['alert_level']}")
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'timestamp': current_metrics.timestamp.isoformat(),
                'error': str(e),
                'alert_level': 'ERROR'
            }
    
    def _extract_alert_level(self, ai_analysis: str) -> str:
        """Extract alert level from AI analysis text"""
        analysis_lower = ai_analysis.lower()
        
        # Look for the overall assessment specifically
        if 'overall assessment: healthy' in analysis_lower or 'overall assessment: normal' in analysis_lower:
            return 'OK'
        elif 'overall assessment: critical' in analysis_lower or 'overall assessment: danger' in analysis_lower:
            return 'CRITICAL'
        elif 'overall assessment: warning' in analysis_lower or 'overall assessment: caution' in analysis_lower:
            return 'WARNING'
        
        # Fallback to general keyword checking with more specific terms
        elif any(phrase in analysis_lower for phrase in ['immediate shutdown', 'critical failure', 'immediate danger']):
            return 'CRITICAL'
        elif any(phrase in analysis_lower for phrase in ['requires attention', 'warning level', 'caution needed']):
            return 'WARNING'
        elif any(word in analysis_lower for word in ['normal', 'healthy', 'good', 'optimal', 'stable']):
            return 'OK'
        else:
            return 'INFO'
    
    def _extract_recommendations(self, ai_analysis: str) -> List[str]:
        """Extract actionable recommendations from AI analysis"""
        recommendations = []
        lines = ai_analysis.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                if line not in recommendations:
                    recommendations.append(line)
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def run_analysis_cycle(self) -> bool:
        """Run a single analysis cycle"""
        try:
            # Collect current metrics
            current_metrics = self.collect_live_metrics()
            if not current_metrics:
                self.logger.warning("Skipping analysis cycle - no live data")
                return False
            
            # Perform analysis
            analysis_result = self.analyze_powertrain_health(current_metrics)
            
            # Log key results
            self.logger.info(f"Analysis cycle completed - Alert: {analysis_result.get('alert_level', 'UNKNOWN')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Analysis cycle failed: {e}")
            return False
    
    def run_continuous(self, interval_minutes: int = 5):
        """Run PowertrainAgent continuously"""
        self.logger.info(f"Starting continuous monitoring (interval: {interval_minutes} minutes)")
        
        while True:
            try:
                cycle_start = time.time()
                
                # Run analysis cycle
                success = self.run_analysis_cycle()
                
                cycle_duration = time.time() - cycle_start
                self.logger.info(f"Analysis cycle took {cycle_duration:.2f} seconds")
                
                # Wait for next cycle
                sleep_time = (interval_minutes * 60) - cycle_duration
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.logger.info("Stopping PowertrainAgent (keyboard interrupt)")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in continuous mode: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='PowertrainAgent - Diesel Generator Powertrain Monitor')
    parser.add_argument('--config', '-c', default='generator_config.yaml',
                      help='Configuration file path')
    parser.add_argument('--interval', '-i', type=int, default=5,
                      help='Analysis interval in minutes (default: 5)')
    parser.add_argument('--bootstrap', action='store_true',
                      help='Bootstrap historical memory from all available data')
    parser.add_argument('--single-run', action='store_true',
                      help='Run single analysis cycle and exit')
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    try:
        # Initialize agent
        agent = PowertrainAgent(args.config)
        
        if args.bootstrap:
            agent.logger.info("Starting historical memory bootstrap...")
            agent.memory_manager.bootstrap_historical_memory()
            agent.logger.info("Historical memory bootstrap completed")
            return
        
        if args.single_run:
            agent.logger.info("Running single analysis cycle...")
            success = agent.run_analysis_cycle()
            sys.exit(0 if success else 1)
        
        # Run continuous monitoring
        agent.run_continuous(args.interval)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()