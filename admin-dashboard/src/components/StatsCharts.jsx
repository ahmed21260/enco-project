import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend, ResponsiveContainer } from 'recharts';
import { collection, onSnapshot } from 'firebase/firestore';
import { db } from '../../firebaseConfig';

const COLORS = ['#007bff', '#28a745', '#fd7e14', '#6f42c1'];

const StatsCharts = () => {
  const [incidentsData, setIncidentsData] = useState([]);
  const [operateursData, setOperateursData] = useState([]);
  const [chantierData, setChantierData] = useState([]);

  useEffect(() => {
    // Incidents par machine (anomalies)
    const unsubAno = onSnapshot(collection(db, 'anomalies'), (snap) => {
      const machines = {};
      snap.docs.forEach(doc => {
        const m = doc.data().machine || 'Inconnu';
        machines[m] = (machines[m] || 0) + 1;
      });
      setIncidentsData(Object.entries(machines).map(([name, value]) => ({ name, value })));
    });
    // Utilisation par opérateur (positions)
    const unsubPos = onSnapshot(collection(db, 'positions_operateurs'), (snap) => {
      const ops = {};
      snap.docs.forEach(doc => {
        const d = doc.data();
        const nom = d.nom || d.operateur_id;
        ops[nom] = (ops[nom] || 0) + 1;
      });
      setOperateursData(Object.entries(ops).map(([name, utilisations]) => ({ name, utilisations })));
    });
    // Bons d'attachement par chantier (exemple fictif, à adapter selon ta BDD)
    const unsubChk = onSnapshot(collection(db, 'checklists'), (snap) => {
      const chantiers = {};
      snap.docs.forEach(doc => {
        const chantier = doc.data().chantier || 'Chantier ?';
        chantiers[chantier] = (chantiers[chantier] || 0) + 1;
      });
      setChantierData(Object.entries(chantiers).map(([name, bons]) => ({ name, bons })));
    });
    return () => { unsubAno(); unsubPos(); unsubChk(); };
  }, []);

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', marginBottom: '2rem' }}>
      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>Bons d'attachement par chantier</h4>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chantierData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="bons" fill="#007bff" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>Incidents par machine</h4>
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie data={incidentsData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
              {incidentsData.map((entry, idx) => (
                <Cell key={`cell-${idx}`} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div style={{ flex: 1, minWidth: 320 }}>
        <h4>Utilisation par opérateur</h4>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={operateursData} layout="vertical">
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" />
            <Tooltip />
            <Bar dataKey="utilisations" fill="#28a745" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default StatsCharts; 