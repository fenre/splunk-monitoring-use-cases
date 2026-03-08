import React, { useState, useEffect } from 'react';
import CategoryList from './CategoryList';
import UseCaseDetail from './UseCaseDetail';

// When loaded from static/index.html, catalog is in same directory
const CATALOG_URL = 'catalog.json';

const styles = { root: { background: '#0f1114', color: '#f0f0f0', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' } };

export default function App() {
  const [catalog, setCatalog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUC, setSelectedUC] = useState(null);

  useEffect(() => {
    fetch(CATALOG_URL)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load catalog: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setCatalog(data);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ ...styles.root, padding: 24, color: '#b0b0b0' }}>Loading Use Case Library…</div>;
  }

  if (error) {
    return (
      <div style={{ ...styles.root, padding: 24, color: '#c45c3e' }}>
        Could not load catalog: {error}. Ensure catalog.json is at appserver/static/catalog.json and rebuild.
      </div>
    );
  }

  if (!catalog || !catalog.DATA) {
    return <div style={{ ...styles.root, padding: 24, color: '#b0b0b0' }}>No catalog data.</div>;
  }

  return (
    <div style={{ ...styles.root, display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <CategoryList
        data={catalog.DATA}
        catMeta={catalog.CAT_META || {}}
        onSelectUseCase={setSelectedUC}
      />
      <UseCaseDetail useCase={selectedUC} onClose={() => setSelectedUC(null)} />
    </div>
  );
}
