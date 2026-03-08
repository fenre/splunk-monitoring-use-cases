import React, { useState } from 'react';

export default function CategoryList({ data, catMeta, onSelectUseCase }) {
  const [openCat, setOpenCat] = useState(null);

  const totalUC = data.reduce((sum, cat) => sum + (cat.s || []).reduce((s, sub) => s + (sub.u || []).length, 0), 0);

  return (
    <div
      style={{
        width: 320,
        minWidth: 320,
        borderRight: '1px solid #3a3f46',
        overflow: 'auto',
        background: '#171a1f',
        padding: 16,
      }}
    >
      <h2 style={{ margin: '0 0 8px', fontSize: 18 }}>Use Case Library</h2>
      <p style={{ color: '#808890', margin: '0 0 16px', fontSize: 13 }}>
        {data.length} categories, {totalUC} use cases
      </p>
      {data.map((cat) => {
        const meta = catMeta[cat.i] || {};
        const icon = meta.icon || '•';
        const isOpen = openCat === cat.i;
        const subCount = (cat.s || []).reduce((s, sub) => s + (sub.u || []).length, 0);
        return (
          <div key={cat.i} style={{ marginBottom: 8 }}>
            <button
              type="button"
              onClick={() => setOpenCat(isOpen ? null : cat.i)}
              style={{
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: 'none',
                border: 'none',
                color: '#00b07c',
                padding: 0,
                fontSize: 14,
                textAlign: 'left',
              }}
            >
              <span>{icon}</span>
              <span>{cat.n}</span>
              <span style={{ color: '#808890', fontSize: 12 }}>({subCount})</span>
            </button>
            {isOpen &&
              (cat.s || []).map((sub, idx) =>
                (sub.u || []).map((uc) => (
                  <div
                    key={uc.id || `${cat.i}-${idx}-${uc.n}`}
                    style={{
                      marginLeft: 24,
                      marginTop: 4,
                      padding: '4px 8px',
                      cursor: 'pointer',
                      borderRadius: 4,
                      fontSize: 13,
                      color: '#b0b0b0',
                    }}
                    onClick={() => onSelectUseCase(uc)}
                    onKeyDown={(e) => e.key === 'Enter' && onSelectUseCase(uc)}
                    role="button"
                    tabIndex={0}
                  >
                    {uc.n}
                  </div>
                ))
              )}
          </div>
        );
      })}
    </div>
  );
}
