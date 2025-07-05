import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend, ResponsiveContainer } from 'recharts';
import { collection, onSnapshot, query, where } from 'firebase/firestore';
import { db } from '../../firebaseConfig';

const COLORS = ['#007bff', '#28a745', '#fd7e14', '#6f42c1', '#e00', '#f90'];

const StatsCharts = () => {
  const [incidentsData, setIncidentsData] = useState([]);
  const [urgencesData, setUrgencesData] = useState([]);
  const [operateursData, setOperateursData] = useState([]);
  const [chantierData, setChantierData] = useState([]);
  const [anomaliesParType, setAnomaliesParType] = useState([]);

  useEffect(() => {
    // Anomalies par machine
    const unsubAno = onSnapshot(collection(db, 'anomalies'), (snap) => {
      const machines = {};
      snap.docs.forEach(doc => {
        const m = doc.data().machine || 'Inconnu';
        machines[m] = (machines[m] || 0) + 1;
      });
      setIncidentsData(Object.entries(machines).map(([name, value]) => ({ name, value })));
    });

    // Urgences par type
    const unsubUrg = onSnapshot(collection(db, 'urgences'), (snap) => {
      const types = {};
      snap.docs.forEach(doc => {
        const type = doc.data().type || 'Autre';
        types[type] = (types[type] || 0) + 1;
      });
      setUrgencesData(Object.entries(types).map(([name, value]) => ({ name, value })));
    });

    // Anomalies par type technique
    const unsubAnoType = onSnapshot(collection(db, 'anomalies'), (snap) => {
      const types = {};
      snap.docs.forEach(doc => {
        const type = doc.data().type_anomalie || 'Non spécifié';
        types[type] = (types[type] || 0) + 1;
      });
      setAnomaliesParType(Object.entries(types).map(([name, value]) => ({ name, value })));
    });

    // Utilisation par opérateur (positions)
    const unsubPos = onSnapshot(collection(db, 'positions_operateurs'), (snap) => {
      const ops = {};
      snap.docs.forEach(doc => {
        const d = doc.data();
        let nom = d.nom && typeof d.nom === 'string' ? d.nom.trim() : '';
        if (!nom || nom.toLowerCase().includes('ferroviaire') || nom.toLowerCase().includes('formation') || nom.toLowerCase().includes('undefined') || nom.length < 2) {
          nom = d.operateur_id || d.telegram_id || 'Inconnu';
        }
        if (!nom || nom === 'undefined' || nom === 'Inconnu') return; // On ne garde pas les barres fantômes
        ops[nom] = (ops[nom] || 0) + 1;
      });
      setOperateursData(Object.entries(ops).map(([name, utilisations]) => ({ name, utilisations })));
    });

    // Bons d'attachement par chantier
    const unsubChk = onSnapshot(collection(db, 'checklists'), (snap) => {
      const chantiers = {};
      snap.docs.forEach(doc => {
        const chantier = doc.data().chantier || 'Chantier ?';
        chantiers[chantier] = (chantiers[chantier] || 0) + 1;
      });
      setChantierData(Object.entries(chantiers).map(([name, bons]) => ({ name, bons })));
    });

    return () => { 
      unsubAno(); 
      unsubUrg(); 
      unsubAnoType();
      unsubPos(); 
      unsubChk(); 
    };
  }, []);

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', marginBottom: '2rem' }}>
      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>🚨 Urgences par type</h4>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={urgencesData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
              {urgencesData.map((entry, idx) => (
                <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>🔧 Anomalies par machine</h4>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={incidentsData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#f90" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>🔧 Anomalies par type technique</h4>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={anomaliesParType} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
              {anomaliesParType.map((entry, idx) => (
                <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>👷 Utilisation par opérateur</h4>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={operateursData} layout="vertical">
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" tick={{ fontSize: 14, width: 120, overflow: 'visible' }} />
            <Tooltip />
            <Bar dataKey="utilisations" fill="#28a745" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>📋 Bons d'attachement par chantier</h4>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chantierData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="bons" fill="#007bff" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default StatsCharts; 