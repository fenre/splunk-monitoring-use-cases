import React from 'react';

export default function UseCaseDetail({ useCase, onClose }) {
  if (!useCase) {
    return (
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#808890',
          padding: 24,
        }}
      >
        Select a use case from the list
      </div>
    );
  }

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 24, background: '#0f1114' }}>
      <button
        type="button"
        onClick={onClose}
        style={{
          marginBottom: 16,
          padding: '8px 16px',
          background: '#262a30',
          border: '1px solid #3a3f46',
          color: '#f0f0f0',
          borderRadius: 4,
          cursor: 'pointer',
        }}
      >
        Close
      </button>
      <h2 style={{ margin: '0 0 8px', fontSize: 20 }}>{useCase.n}</h2>
      {useCase.id && (
        <p style={{ color: '#808890', marginBottom: 8, fontSize: 13 }}>
          <code style={{ background: '#171a1f', padding: '2px 6px', borderRadius: 4 }}>{useCase.id}</code>
        </p>
      )}
      {useCase.t && (
        <div style={{ marginBottom: 12, fontSize: 14 }}>
          <strong style={{ color: '#b0b0b0' }}>App / TA:</strong> {useCase.t}
        </div>
      )}
      {useCase.d && (
        <div style={{ marginBottom: 12, fontSize: 14 }}>
          <strong style={{ color: '#b0b0b0' }}>Data sources:</strong> {useCase.d}
        </div>
      )}
      {useCase.m && (
        <div style={{ marginBottom: 12, fontSize: 14 }}>
          <strong style={{ color: '#b0b0b0' }}>Implementation:</strong>
          <p style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{useCase.m}</p>
        </div>
      )}
      {useCase.q && (
        <div style={{ marginBottom: 12, fontSize: 14 }}>
          <strong style={{ color: '#b0b0b0' }}>SPL:</strong>
          <pre
            style={{
              background: '#171a1f',
              padding: 12,
              borderRadius: 4,
              overflow: 'auto',
              fontSize: 12,
              marginTop: 4,
            }}
          >
            <code>{useCase.q}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
