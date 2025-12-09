// frontend/src/components/StrategyTable.jsx

import React from "react";

function StrategyTable({ title, data, dealerHeaders, rowLabelPrefix, isPairs }) {
  if (!data || Object.keys(data).length === 0) {
    return null;
  }

  const rowKeys = Object.keys(data).sort((a, b) => {
    // Tri numérique, avec "A" traité comme 11 pour les paires
    const parse = (x) => (x === "A" ? 11 : Number(x));
    return parse(a) - parse(b);
  });

  return (
    <div className="strategy-table-wrapper">
      <h3>{title}</h3>
      <div className="table-scroll">
        <table className="strategy-table">
          <thead>
            <tr>
              <th className="player-header">Joueur</th>
              {dealerHeaders.map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rowKeys.map((rowKey) => {
              const row = data[rowKey];
              const label = isPairs ? `${rowKey}${rowLabelPrefix}${rowKey}` : rowKey;
              return (
                <tr key={rowKey}>
                  <td className="player-header">{label}</td>
                  {dealerHeaders.map((h) => {
                    const action = row[h];
                    const className = `action-cell action-${action}`;
                    return (
                      <td key={h} className={className}>
                        {action}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default StrategyTable;
