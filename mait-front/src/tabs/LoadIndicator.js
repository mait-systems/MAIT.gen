import React, { useEffect, useState } from 'react';
import axios from 'axios';
import ChartBox from '../components/ChartBox';

const LoadIndicator = () => {
  const [engineRPM, setEngineRPM] = useState(0);
  const [load, setLoad] = useState(0);
  const [coolantTemp, setCoolantTemp] = useState(0);

  const fetchLoadData = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || ''}/api/live-stats`);

      const rawEngineRPM = response.data['Engine_Speed'];
      const rawLoad = response.data['Generator_Apparent_Power'];
      const rawCoolantTemp = response.data['Engine_Coolant_Temperature'];

      if (typeof rawEngineRPM === 'number' && !isNaN(rawEngineRPM)) {
        setEngineRPM(rawEngineRPM);
      } else {
        setEngineRPM(0);
      }

      if (typeof rawLoad === 'number' && !isNaN(rawLoad)) {
        setLoad(Math.min(rawLoad, 100));
      } else {
        setLoad(0);
      }

      if (typeof rawCoolantTemp === 'number' && !isNaN(rawCoolantTemp)) {
        setCoolantTemp(rawCoolantTemp);
      } else {
        setCoolantTemp(0);
      }

    } catch (error) {
      console.error("Error fetching load data", error);
    }
  };

  useEffect(() => {
    fetchLoadData();
    const interval = setInterval(fetchLoadData, 2000);
    return () => clearInterval(interval);
  }, []);


  const getRPMColor = (rpm) => {
  if (rpm >= 1798 && rpm <= 1802) return "#4CAF50"; // Green for normal range
  if (rpm < 1798) return "#FFBB33"; // Yellow if too low
  return "#FF4C4C"; // Red if too high
  };
  
  const getColor = (value) => {
    if (value <= 50) return "#4CAF50";
    if (value <= 80) return "#FFBB33";
    return "#FF4C4C";
  };

  const getCoolantColor = (temp) => {
    if (temp <= 92) return "#2196F3";
    if (temp <= 120) return "#FFBB33";
    return "#FF4C4C";
  };

  const chartDataRPM = [{ name: '', value: engineRPM }];
  const chartDataLoad = [{ name: '', value: load }];
  const chartDataCoolant = [{ name: '', value: coolantTemp }];

  return (
    <div style={{ width: '100%', marginTop: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <ChartBox title="Engine RPM" chartData={chartDataRPM} colorFunc={getColor} yAxisDomain={[0, 2000]} />
        <ChartBox title="Generator Load" chartData={chartDataLoad} colorFunc={getColor} />
        <ChartBox title="Engine Coolant T (°C)" chartData={chartDataCoolant} colorFunc={getCoolantColor} yAxisDomain={[0, 120]} />
      </div>
    </div>
  );
};

export default LoadIndicator;