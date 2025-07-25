#!/usr/bin/env python3
"""
Memory-Enhanced Prompt Builder for PowertrainAgent
Creates intelligent prompts that incorporate historical memory and accumulated knowledge
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from openai import OpenAI

from memory_manager import MemoryContext

class MemoryEnhancedPromptBuilder:
    """
    Builds comprehensive AI prompts that incorporate:
    - Current powertrain metrics
    - Historical baseline comparisons
    - Event memory and patterns
    - Accumulated AI insights
    - Degradation trends and predictions
    """
    
    def __init__(self, config: dict):
        """Initialize prompt builder with OpenAI client"""
        self.config = config
        openai_config = config.get('openai', {})
        
        self.openai_client = OpenAI(
            api_key=openai_config.get('api_key', '')
        )
        
        self.logger = logging.getLogger('MemoryEnhancedPromptBuilder')
        self.logger.info("Memory-Enhanced Prompt Builder initialized")
    
    def build_analysis_prompt(self, current_metrics, memory_context: MemoryContext) -> str:
        """
        Build comprehensive analysis prompt with memory context
        
        Args:
            current_metrics: PowertrainMetrics object with current data
            memory_context: MemoryContext with historical information
            
        Returns:
            Formatted prompt string for AI analysis
        """
        try:
            # Build prompt sections
            header = self._build_prompt_header()
            current_section = self._build_current_metrics_section(current_metrics)
            memory_section = self._build_memory_section(memory_context)
            guidance_section = self._build_analysis_guidance()
            
            # Combine all sections
            full_prompt = f"""
{header}

{current_section}

{memory_section}

{guidance_section}
"""
            
            self.logger.debug(f"Built analysis prompt with {len(full_prompt)} characters")
            return full_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to build analysis prompt: {e}")
            return self._build_fallback_prompt(current_metrics)
    
    def _build_prompt_header(self) -> str:
        """Build the prompt header with context"""
        return """# Kohler 150kW Diesel Generator - PowertrainAgent Analysis

You are an expert diesel generator engineer with cumulative knowledge from continuous monitoring of this specific Kohler 150kW, 6-cylinder diesel generator. You have access to both real-time data and extensive historical memory from past operations.

## Generator Specifications:
- **Model**: Kohler 150kW Diesel Generator
- **Engine**: 6-cylinder diesel, 1800 RPM rated
- **Power Rating**: 150kW at 208V, 520A, 60Hz
- **Maintenance Schedule**: Every 250 hours (250, 500, 750, 1000, etc.)
- **Controller**: ECM Model 33 with Modbus TCP interface

## Your Role:
As PowertrainAgent, you provide intelligent analysis of mechanical and lubrication health by combining current telemetry with your accumulated operational memory. Focus on powertrain-specific insights: engine performance, oil system health, load efficiency, and predictive maintenance."""
    
    def _build_current_metrics_section(self, current_metrics) -> str:
        """Build current metrics section of prompt"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine operational status
        if current_metrics.engine_speed > 100:
            status = "RUNNING"
            status_context = f"Engine operating at {current_metrics.engine_speed:.0f} RPM"
        else:
            status = "STOPPED"
            status_context = "Engine currently stopped (0 RPM)"
        
        # Power output analysis
        power_status = self._analyze_power_output(current_metrics.generator_total_real_power)
        
        # Oil pressure analysis
        oil_status = self._analyze_oil_pressure(current_metrics.engine_oil_pressure, current_metrics.engine_speed)
        
        return f"""
## CURRENT POWERTRAIN STATUS ({timestamp})
**Operational State**: {status} - {status_context}
**Load Band**: {current_metrics.load_band}

### Key Metrics:
| Metric | Current Value | Status |
|--------|---------------|--------|
| Engine Speed | {current_metrics.engine_speed:.1f} RPM | {self._get_rpm_status(current_metrics.engine_speed, current_metrics.engine_run_speed)} |
| Target Speed | {current_metrics.engine_run_speed:.1f} RPM | - |
| Oil Pressure | {current_metrics.engine_oil_pressure:.1f} kPa | {oil_status} |
| Power Output | {current_metrics.generator_total_real_power:.1f}% | {power_status} |
| Coolant Temp | {current_metrics.engine_coolant_temperature:.1f}°C | {self._get_temp_status(current_metrics.engine_coolant_temperature)} |

### Performance Indicators:
- **RPM Stability**: {abs(current_metrics.engine_speed - current_metrics.engine_run_speed):.1f} RPM deviation from target
- **Load Efficiency**: {current_metrics.generator_total_real_power:.1f}% of rated capacity
- **Lubrication Health**: {oil_status.lower()} oil pressure for current operating conditions
"""
    
    def _build_memory_section(self, memory_context: MemoryContext) -> str:
        """Build historical memory section of prompt"""
        # Historical baselines summary
        baselines_summary = self._summarize_baselines(memory_context.historical_baselines)
        
        # Recent events summary
        events_summary = self._summarize_recent_events(memory_context.recent_events)
        
        # Trends summary
        trends_summary = self._summarize_trends(memory_context.degradation_trends)
        
        # Runtime context
        runtime_context = self._build_runtime_context(memory_context.total_runtime_hours)
        
        return f"""
## HISTORICAL MEMORY & CONTEXT

### Operational History:
{runtime_context}

### Load Band Historical Performance ({memory_context.current_load_band}):
{baselines_summary}

### Recent Event Memory (Last 7 Days):
{events_summary}

### Long-term Trends:
{trends_summary}

### Accumulated Intelligence:
{self._format_ai_insights(memory_context.ai_insights)}

### Seasonal Context:
{self._format_seasonal_patterns(memory_context.seasonal_patterns)}
"""
    
    def _summarize_baselines(self, baselines: List) -> str:
        """Summarize historical baselines for the prompt"""
        if not baselines:
            return "No historical baseline data available for this load band."
        
        # Calculate averages from recent baselines
        recent_baselines = baselines[-7:]  # Last 7 periods
        
        if not recent_baselines:
            return "Insufficient baseline data for comparison."
        
        avg_oil_pressure = sum(b.avg_oil_pressure for b in recent_baselines) / len(recent_baselines)
        avg_engine_speed = sum(b.avg_engine_speed for b in recent_baselines) / len(recent_baselines)
        
        # Calculate variability
        oil_variability = sum(b.stddev_oil_pressure for b in recent_baselines) / len(recent_baselines)
        
        return f"""
- **Typical Oil Pressure**: {avg_oil_pressure:.1f} ± {oil_variability:.1f} kPa (based on {len(recent_baselines)} recent periods)
- **Typical Engine Speed**: {avg_engine_speed:.1f} RPM
- **Data Quality**: {sum(b.sample_count for b in recent_baselines)} historical data points
- **Trend Confidence**: {sum(b.confidence_level for b in recent_baselines) / len(recent_baselines):.2f}
"""
    
    def _summarize_recent_events(self, events: List[dict]) -> str:
        """Summarize recent events for context"""
        if not events:
            return "No significant events in recent history."
        
        # Categorize events
        critical_events = [e for e in events if e.get('severity') == 'CRITICAL']
        warning_events = [e for e in events if e.get('severity') == 'WARNING']
        
        summary = []
        
        if critical_events:
            summary.append(f"🔴 **{len(critical_events)} Critical Events** - Immediate attention required")
            for event in critical_events[:2]:  # Show top 2
                summary.append(f"   - {event.get('description', 'Unknown event')}")
        
        if warning_events:
            summary.append(f"🟡 **{len(warning_events)} Warning Events** - Monitor closely")
            for event in warning_events[:2]:  # Show top 2
                summary.append(f"   - {event.get('description', 'Unknown event')}")
        
        if not summary:
            summary.append("✅ **No Critical or Warning Events** - Normal operation patterns")
        
        return '\n'.join(summary)
    
    def _summarize_trends(self, trends: Dict[str, Any]) -> str:
        """Summarize degradation trends"""
        if not trends:
            return "Trend analysis pending - insufficient historical data."
        
        summary = []
        for metric, trend in trends.items():
            if isinstance(trend, str):
                summary.append(f"- **{metric.replace('_', ' ').title()}**: {trend}")
            else:
                summary.append(f"- **{metric.replace('_', ' ').title()}**: Analysis in progress")
        
        return '\n'.join(summary) if summary else "No significant trends detected."
    
    def _build_runtime_context(self, total_hours: float) -> str:
        """Build runtime and maintenance context"""
        # Calculate maintenance scheduling
        hours_since_last_service = total_hours % 250
        hours_to_next_service = 250 - hours_since_last_service
        
        if hours_to_next_service <= 25:
            maintenance_status = f"🔧 **MAINTENANCE DUE SOON** - {hours_to_next_service:.1f} hours remaining"
        elif hours_to_next_service <= 50:
            maintenance_status = f"🟡 **Approaching Service** - {hours_to_next_service:.1f} hours to 250hr service"
        else:
            maintenance_status = f"✅ **Service Current** - {hours_to_next_service:.1f} hours to next 250hr service"
        
        return f"""
- **Total Runtime**: {total_hours:.1f} hours
- **Maintenance Status**: {maintenance_status}
- **Service Intervals**: 250hr cycles (Next: {total_hours - hours_since_last_service + 250:.0f}hr mark)
- **Operating Experience**: {int(total_hours / 24):.0f} equivalent days of runtime data
"""
    
    def _format_ai_insights(self, insights: List[dict]) -> str:
        """Format accumulated AI insights"""
        if not insights:
            return "Building knowledge base - initial analysis phase."
        
        formatted = []
        for insight in insights[:3]:  # Top 3 insights
            formatted.append(f"- {insight.get('text', 'Insight processing...')}")
        
        return '\n'.join(formatted)
    
    def _format_seasonal_patterns(self, patterns: Dict[str, Any]) -> str:
        """Format seasonal pattern information"""
        if not patterns:
            return "Seasonal pattern analysis in progress."
        
        formatted = []
        for pattern_type, data in patterns.items():
            if isinstance(data, bool):
                status = "Normal" if data else "Unusual"
                formatted.append(f"- **{pattern_type.replace('_', ' ').title()}**: {status}")
            else:
                formatted.append(f"- **{pattern_type.replace('_', ' ').title()}**: Pattern detected")
        
        return '\n'.join(formatted) if formatted else "No significant seasonal patterns identified."
    
    def _build_analysis_guidance(self) -> str:
        """Build analysis guidance section"""
        return """
## ANALYSIS REQUIREMENTS

### Focus Areas:
1. **Oil System Health**: Pressure trends, viscosity indicators, pump performance
2. **Engine Performance**: RPM stability, load response, efficiency patterns
3. **Wear Indicators**: Long-term degradation patterns, maintenance predictors
4. **Anomaly Detection**: Deviations from historical baselines and patterns

### Analysis Format:
Provide your analysis in the following structure:

#### 🔧 **POWERTRAIN HEALTH SUMMARY**
Overall assessment: [HEALTHY/MONITOR/WARNING/CRITICAL]

#### 📊 **KEY FINDINGS**
- Oil pressure analysis vs historical norms
- Engine performance vs load expectations
- Any significant deviations or concerns

#### 📈 **TREND ANALYSIS**
- Comparison to historical patterns
- Long-term trend indicators
- Predictive insights

#### ⚠️ **RECOMMENDATIONS**
- Immediate actions (if any)
- Monitoring priorities
- Maintenance scheduling insights

#### 🧠 **MEMORY NOTES**
- Patterns to remember for future analysis
- Learning updates from this analysis
- Context for next evaluation

### Remember:
- You have continuous memory of this specific generator's history
- Compare current data against YOUR accumulated knowledge
- Identify both short-term anomalies and long-term trends
- Provide actionable insights based on your operational experience with this unit
"""
    
    def _analyze_power_output(self, power_pct: float) -> str:
        """Analyze power output status"""
        if power_pct < 5:
            return "No Load"
        elif power_pct < 25:
            return "Light Load"
        elif power_pct < 50:
            return "Moderate Load"
        elif power_pct < 75:
            return "Heavy Load"
        else:
            return "Maximum Load"
    
    def _analyze_oil_pressure(self, pressure: float, rpm: float) -> str:
        """Analyze oil pressure status"""
        if rpm < 100:  # Engine stopped
            return "Normal (Engine Stopped)"
        elif pressure < 200:
            return "LOW - Monitor Closely"
        elif pressure < 350:
            return "Below Normal"
        elif pressure < 600:
            return "Normal"
        else:
            return "High"
    
    def _get_rpm_status(self, actual: float, target: float) -> str:
        """Get RPM status vs target"""
        if actual < 100:
            return "Stopped"
        
        deviation = abs(actual - target)
        if deviation < 25:
            return "Stable"
        elif deviation < 50:
            return "Minor Deviation"
        else:
            return "Significant Deviation"
    
    def _get_temp_status(self, temp: float) -> str:
        """Get temperature status"""
        if temp < 40:
            return "Cold"
        elif temp < 80:
            return "Normal"
        elif temp < 100:
            return "Warm"
        else:
            return "Hot"
    
    def get_ai_analysis(self, prompt: str) -> str:
        """
        Get AI analysis from OpenAI using the constructed prompt
        
        Args:
            prompt: Complete analysis prompt
            
        Returns:
            AI analysis response
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are PowertrainAgent, an expert diesel generator engineer with continuous memory of this specific generator's operational history. Provide detailed, technical analysis based on your accumulated knowledge."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent technical analysis
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            self.logger.info(f"Generated AI analysis ({len(analysis)} characters)")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            return f"Analysis temporarily unavailable: {str(e)}"
    
    def _build_fallback_prompt(self, current_metrics) -> str:
        """Build a basic fallback prompt if memory context fails"""
        return f"""
Analyze the current powertrain status of a Kohler 150kW diesel generator:

Current Metrics:
- Engine Speed: {current_metrics.engine_speed:.1f} RPM
- Target Speed: {current_metrics.engine_run_speed:.1f} RPM  
- Oil Pressure: {current_metrics.engine_oil_pressure:.1f} kPa
- Power Output: {current_metrics.generator_total_real_power:.1f}%
- Coolant Temperature: {current_metrics.engine_coolant_temperature:.1f}°C
- Load Band: {current_metrics.load_band}

Provide a brief health assessment focusing on oil pressure, engine performance, and any immediate concerns.
"""