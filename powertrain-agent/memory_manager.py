#!/usr/bin/env python3
"""
PowertrainMemoryManager - Persistent memory system for PowertrainAgent
Manages historical baselines, event memory, and AI knowledge accumulation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import logging
from scipy import stats
from collections import defaultdict

from influx_query import InfluxQueryManager, HistoricalSummary

@dataclass
class MemoryContext:
    """Memory context for analysis"""
    current_load_band: str
    historical_baselines: List[HistoricalSummary]
    recent_events: List[dict]
    ai_insights: List[dict]
    degradation_trends: Dict[str, float]
    seasonal_patterns: Dict[str, Any]
    total_runtime_hours: float
    maintenance_history: List[dict]

class PowertrainMemoryManager:
    """
    Manages persistent memory for PowertrainAgent including:
    - Rolling historical baselines
    - Event pattern recognition
    - AI knowledge accumulation
    - Trend analysis and degradation tracking
    """
    
    def __init__(self, config: dict):
        """Initialize memory manager"""
        self.config = config
        self.influx_manager = InfluxQueryManager(config)
        self.logger = logging.getLogger('PowertrainMemoryManager')
        
        # Memory configuration
        self.baseline_periods = ['hourly', 'daily', 'weekly', 'monthly']
        self.load_bands = ['0%', '0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
        
        # Bootstrap flag
        self.memory_bootstrapped = False
        
        self.logger.info("PowertrainMemoryManager initialized")
    
    def bootstrap_historical_memory(self) -> bool:
        """
        Bootstrap the memory system by processing ALL historical data
        This creates the initial baseline knowledge from existing data
        
        Returns:
            True if bootstrap successful, False otherwise
        """
        try:
            self.logger.info("Starting historical memory bootstrap...")
            
            # Step 1: Get all historical data
            all_data = self.influx_manager.get_all_historical_data()
            if all_data is None or all_data.empty:
                self.logger.warning("No historical data available for bootstrap")
                return False
            
            self.logger.info(f"Processing {len(all_data)} historical data points")
            
            # Step 2: Create baseline summaries for each time period and load band
            self._create_baseline_summaries(all_data)
            
            # Step 3: Identify significant events in historical data
            self._identify_historical_events(all_data)
            
            # Step 4: Calculate degradation trends
            self._calculate_degradation_trends(all_data)
            
            # Step 5: Identify seasonal patterns
            self._identify_seasonal_patterns(all_data)
            
            self.memory_bootstrapped = True
            self.logger.info("Historical memory bootstrap completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Bootstrap failed: {e}")
            return False
    
    def _create_baseline_summaries(self, data: pd.DataFrame):
        """Create baseline summaries for different time periods and load bands"""
        try:
            for period in self.baseline_periods:
                self.logger.info(f"Creating {period} baselines...")
                
                # Define time grouping
                if period == 'hourly':
                    time_group = data['_time'].dt.floor('H')
                    window_hours = 1
                elif period == 'daily':
                    time_group = data['_time'].dt.floor('D')
                    window_hours = 24
                elif period == 'weekly':
                    time_group = data['_time'].dt.floor('W')
                    window_hours = 168
                else:  # monthly
                    time_group = data['_time'].dt.floor('M')
                    window_hours = 720
                
                # Group by time period and load band
                for load_band in self.load_bands:
                    band_data = data[data['load_band'] == load_band].copy()
                    if band_data.empty:
                        continue
                    
                    band_data['time_group'] = time_group[band_data.index]
                    
                    # Calculate statistics for each time group
                    for time_val, group in band_data.groupby('time_group'):
                        if len(group) < 3:  # Need minimum data points
                            continue
                        
                        baseline = self._calculate_baseline_stats(group, load_band, period, time_val)
                        if baseline:
                            self.influx_manager.store_historical_baseline(baseline)
            
            self.logger.info("Baseline summaries created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create baseline summaries: {e}")
    
    def _calculate_baseline_stats(self, group: pd.DataFrame, load_band: str, 
                                period: str, time_val: datetime) -> Optional[HistoricalSummary]:
        """Calculate statistical baseline from a group of data points"""
        try:
            # Calculate basic statistics
            metrics = {
                'Engine_Speed': group['Engine_Speed'].dropna(),
                'Engine_Run_Speed': group['Engine_Run_Speed'].dropna(),
                'Engine_Oil_Pressure': group['Engine_Oil_Pressure'].dropna(),
                'Generator_Total_Real_Power': group['Generator_Total_Real_Power'].dropna()
            }
            
            # Skip if not enough data
            if any(len(values) < 3 for values in metrics.values()):
                return None
            
            # Calculate trend slope for oil pressure (key health indicator)
            oil_pressure = metrics['Engine_Oil_Pressure']
            if len(oil_pressure) > 5:
                x = np.arange(len(oil_pressure))
                slope, _, r_value, _, _ = stats.linregress(x, oil_pressure)
                trend_slope = slope
                confidence = abs(r_value)
            else:
                trend_slope = 0.0
                confidence = 0.0
            
            # Create baseline summary
            baseline = HistoricalSummary(
                load_band=load_band,
                time_period=period,
                avg_engine_speed=float(metrics['Engine_Speed'].mean()),
                avg_run_speed=float(metrics['Engine_Run_Speed'].mean()),
                avg_oil_pressure=float(oil_pressure.mean()),
                avg_power_output=float(metrics['Generator_Total_Real_Power'].mean()),
                stddev_engine_speed=float(metrics['Engine_Speed'].std()),
                stddev_oil_pressure=float(oil_pressure.std()),
                sample_count=len(group),
                min_oil_pressure=float(oil_pressure.min()),
                max_oil_pressure=float(oil_pressure.max()),
                trend_slope=trend_slope,
                confidence_level=confidence,
                start_time=group['_time'].min(),
                end_time=group['_time'].max()
            )
            
            return baseline
            
        except Exception as e:
            self.logger.debug(f"Failed to calculate baseline stats: {e}")
            return None
    
    def _identify_historical_events(self, data: pd.DataFrame):
        """Identify significant events in historical data"""
        try:
            self.logger.info("Identifying historical events...")
            
            # Event detection thresholds
            thresholds = {
                'oil_pressure_low': 200,  # kPa
                'oil_pressure_drop': 50,  # kPa sudden drop
                'rpm_deviation': 100,     # RPM from target
                'power_spike': 20         # % sudden change
            }
            
            events_found = 0
            
            # Sort by time for sequential analysis
            data_sorted = data.sort_values('_time')
            
            # Rolling window analysis for anomaly detection
            window_size = 20  # 20 data points
            
            for i in range(window_size, len(data_sorted)):
                current = data_sorted.iloc[i]
                window = data_sorted.iloc[i-window_size:i]
                
                # Check for oil pressure anomalies
                if current['Engine_Oil_Pressure'] < thresholds['oil_pressure_low']:
                    self._store_historical_event(
                        'anomaly', 'WARNING', 
                        f"Low oil pressure detected: {current['Engine_Oil_Pressure']:.1f} kPa",
                        {
                            'oil_pressure': current['Engine_Oil_Pressure'],
                            'load_band': current['load_band'],
                            'timestamp': current['_time'].isoformat()
                        }
                    )
                    events_found += 1
                
                # Check for sudden oil pressure drops
                recent_avg = window['Engine_Oil_Pressure'].mean()
                if (recent_avg - current['Engine_Oil_Pressure']) > thresholds['oil_pressure_drop']:
                    self._store_historical_event(
                        'anomaly', 'CRITICAL',
                        f"Sudden oil pressure drop: {recent_avg:.1f} to {current['Engine_Oil_Pressure']:.1f} kPa",
                        {
                            'pressure_drop': recent_avg - current['Engine_Oil_Pressure'],
                            'load_band': current['load_band'],
                            'timestamp': current['_time'].isoformat()
                        }
                    )
                    events_found += 1
                
                # Check for RPM deviations
                rpm_diff = abs(current['Engine_Speed'] - current['Engine_Run_Speed'])
                if rpm_diff > thresholds['rpm_deviation']:
                    self._store_historical_event(
                        'operational', 'WARNING',
                        f"RPM deviation: {rpm_diff:.1f} RPM from target",
                        {
                            'actual_rpm': current['Engine_Speed'],
                            'target_rpm': current['Engine_Run_Speed'],
                            'deviation': rpm_diff,
                            'timestamp': current['_time'].isoformat()
                        }
                    )
                    events_found += 1
            
            self.logger.info(f"Identified {events_found} historical events")
            
        except Exception as e:
            self.logger.error(f"Failed to identify historical events: {e}")
    
    def _store_historical_event(self, event_type: str, severity: str, 
                              description: str, context: dict):
        """Store a historical event in memory"""
        self.influx_manager.store_event_memory(
            event_type=event_type,
            severity=severity,
            description=description,
            context_data=context
        )
    
    def _calculate_degradation_trends(self, data: pd.DataFrame):
        """Calculate long-term degradation trends for key metrics"""
        try:
            self.logger.info("Calculating degradation trends...")
            
            # Group by load band for trend analysis
            for load_band in self.load_bands:
                band_data = data[data['load_band'] == load_band]
                if band_data.empty or len(band_data) < 10:
                    continue
                
                # Sort by time
                band_data = band_data.sort_values('_time')
                
                # Calculate trends for key metrics
                trends = {}
                metrics = ['Engine_Oil_Pressure', 'Engine_Speed', 'Generator_Total_Real_Power']
                
                for metric in metrics:
                    values = band_data[metric].dropna()
                    if len(values) > 10:
                        x = np.arange(len(values))
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                        
                        trends[metric] = {
                            'slope': slope,
                            'r_squared': r_value**2,
                            'significance': p_value,
                            'trend_direction': 'declining' if slope < 0 else 'stable' if abs(slope) < 0.01 else 'increasing'
                        }
                
                # Store significant trends as AI memory
                for metric, trend in trends.items():
                    if trend['significance'] < 0.05 and abs(trend['slope']) > 0.01:  # Statistically significant
                        insight_text = (f"{metric} showing {trend['trend_direction']} trend "
                                      f"in {load_band} load band (R²={trend['r_squared']:.3f})")
                        
                        self.influx_manager.store_ai_memory(
                            knowledge_type='trend',
                            insight_text=insight_text,
                            supporting_metrics=trend,
                            confidence='high' if trend['r_squared'] > 0.7 else 'medium'
                        )
            
            self.logger.info("Degradation trends calculated")
            
        except Exception as e:
            self.logger.error(f"Failed to calculate degradation trends: {e}")
    
    def _identify_seasonal_patterns(self, data: pd.DataFrame):
        """Identify seasonal patterns in the data"""
        try:
            self.logger.info("Identifying seasonal patterns...")
            
            # Add time-based features
            data['hour'] = data['_time'].dt.hour
            data['day_of_week'] = data['_time'].dt.dayofweek
            data['month'] = data['_time'].dt.month
            
            seasonal_patterns = {}
            
            # Hourly patterns
            hourly_oil_pressure = data.groupby('hour')['Engine_Oil_Pressure'].mean()
            if hourly_oil_pressure.std() > 5:  # Significant variation
                peak_hour = hourly_oil_pressure.idxmax()
                low_hour = hourly_oil_pressure.idxmin()
                seasonal_patterns['hourly'] = {
                    'pattern_type': 'hourly_oil_pressure',
                    'peak_hour': int(peak_hour),
                    'low_hour': int(low_hour),
                    'variation': float(hourly_oil_pressure.std())
                }
            
            # Daily patterns
            daily_load = data.groupby('day_of_week')['Generator_Total_Real_Power'].mean()
            if daily_load.std() > 5:  # Significant variation
                seasonal_patterns['daily'] = {
                    'pattern_type': 'daily_load',
                    'weekday_avg': float(daily_load[0:5].mean()),
                    'weekend_avg': float(daily_load[5:7].mean()),
                    'variation': float(daily_load.std())
                }
            
            # Store patterns as AI memory
            for period, pattern in seasonal_patterns.items():
                insight_text = f"Identified {period} seasonal pattern: {pattern['pattern_type']}"
                
                self.influx_manager.store_ai_memory(
                    knowledge_type='pattern',
                    insight_text=insight_text,
                    supporting_metrics=pattern,
                    confidence='medium'
                )
            
            self.logger.info(f"Identified {len(seasonal_patterns)} seasonal patterns")
            
        except Exception as e:
            self.logger.error(f"Failed to identify seasonal patterns: {e}")
    
    def update_memory_incremental(self, current_metrics) -> bool:
        """
        Update memory system incrementally with new data
        
        Args:
            current_metrics: PowertrainMetrics object with current data
            
        Returns:
            True if update successful
        """
        try:
            # Check if we need to create new baselines
            self._update_baselines_incremental(current_metrics)
            
            # Check for anomalies in current data
            self._detect_current_anomalies(current_metrics)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Incremental memory update failed: {e}")
            return False
    
    def _update_baselines_incremental(self, current_metrics):
        """Update baseline statistics with new data point"""
        # This would implement incremental statistics updates
        # For now, we'll do periodic full recalculations
        pass
    
    def _detect_current_anomalies(self, current_metrics):
        """Detect anomalies in current metrics and store as events"""
        try:
            # Get recent baselines for comparison
            baselines = self.influx_manager.get_historical_baselines(
                current_metrics.load_band, 'daily', 7
            )
            
            if not baselines:
                return
            
            # Calculate recent averages
            recent_avg_oil = np.mean([b.avg_oil_pressure for b in baselines])
            recent_std_oil = np.mean([b.stddev_oil_pressure for b in baselines])
            
            # Check for anomalies (2-sigma rule)
            oil_pressure = current_metrics.engine_oil_pressure
            if abs(oil_pressure - recent_avg_oil) > 2 * recent_std_oil:
                severity = 'WARNING' if abs(oil_pressure - recent_avg_oil) < 3 * recent_std_oil else 'CRITICAL'
                
                self.influx_manager.store_event_memory(
                    event_type='anomaly',
                    severity=severity,
                    description=f"Oil pressure anomaly: {oil_pressure:.1f} kPa (expected: {recent_avg_oil:.1f}±{recent_std_oil:.1f})",
                    context_data={
                        'current_oil_pressure': oil_pressure,
                        'expected_range': [recent_avg_oil - 2*recent_std_oil, recent_avg_oil + 2*recent_std_oil],
                        'load_band': current_metrics.load_band,
                        'deviation_sigma': abs(oil_pressure - recent_avg_oil) / recent_std_oil
                    }
                )
        
        except Exception as e:
            self.logger.debug(f"Anomaly detection failed: {e}")
    
    def get_analysis_context(self, current_metrics) -> MemoryContext:
        """
        Build comprehensive memory context for analysis
        
        Args:
            current_metrics: PowertrainMetrics object
            
        Returns:
            MemoryContext with all relevant historical information
        """
        try:
            # Get historical baselines for current load band
            baselines = self.influx_manager.get_historical_baselines(
                current_metrics.load_band, 'hourly', 30
            )
            
            # Get recent events
            recent_events = self.influx_manager.get_recent_events(7)
            
            # Get AI insights (placeholder - would query powertrain_ai_memory)
            ai_insights = []
            
            # Calculate degradation trends (simplified)
            degradation_trends = {
                'oil_pressure_trend': 'stable',
                'efficiency_trend': 'stable'
            }
            
            # Seasonal patterns (placeholder)
            seasonal_patterns = {
                'current_hour_typical': True,
                'load_pattern_normal': True
            }
            
            # Maintenance history (from generator config data)
            total_runtime = 2341.9  # Would get from latest data
            
            context = MemoryContext(
                current_load_band=current_metrics.load_band,
                historical_baselines=baselines,
                recent_events=recent_events,
                ai_insights=ai_insights,
                degradation_trends=degradation_trends,
                seasonal_patterns=seasonal_patterns,
                total_runtime_hours=total_runtime,
                maintenance_history=[]
            )
            
            self.logger.debug(f"Built analysis context with {len(baselines)} baselines, {len(recent_events)} events")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to build analysis context: {e}")
            # Return minimal context
            return MemoryContext(
                current_load_band=current_metrics.load_band,
                historical_baselines=[],
                recent_events=[],
                ai_insights=[],
                degradation_trends={},
                seasonal_patterns={},
                total_runtime_hours=0,
                maintenance_history=[]
            )
    
    def update_ai_memory(self, analysis_result: dict):
        """
        Update AI memory with new analysis insights
        
        Args:
            analysis_result: Dictionary containing analysis results
        """
        try:
            ai_analysis = analysis_result.get('ai_analysis', '')
            
            # Extract key insights from AI analysis
            insights = self._extract_insights_from_analysis(ai_analysis)
            
            for insight in insights:
                self.influx_manager.store_ai_memory(
                    knowledge_type=insight['type'],
                    insight_text=insight['text'],
                    supporting_metrics=insight['metrics'],
                    confidence=insight['confidence']
                )
                
        except Exception as e:
            self.logger.error(f"Failed to update AI memory: {e}")
    
    def _extract_insights_from_analysis(self, ai_analysis: str) -> List[dict]:
        """Extract structured insights from AI analysis text"""
        insights = []
        
        # Simple pattern matching for insights
        lines = ai_analysis.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            if 'trend' in line and ('oil' in line or 'pressure' in line):
                insights.append({
                    'type': 'trend',
                    'text': line,
                    'metrics': {},
                    'confidence': 'medium'
                })
            elif 'pattern' in line or 'recurring' in line:
                insights.append({
                    'type': 'pattern',
                    'text': line,
                    'metrics': {},
                    'confidence': 'medium'
                })
        
        return insights[:3]  # Limit to top 3 insights