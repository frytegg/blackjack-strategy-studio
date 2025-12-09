// frontend/src/components/StrategyTables.jsx

import React from "react";
import StrategyTable from "./StrategyTable";

function StrategyTables({ strategy }) {
  const { hard, soft, pairs } = strategy;

  // Construire la liste des colonnes (upcards du croupier) à partir du premier row de "hard"
  const dealerHeaders = hard
    ? Object.keys(Object.values(hard)[0] || {})
    : [];

  return (
    <div className="tables-container">
      <StrategyTable
        title="Hard totals"
        data={hard}
        dealerHeaders={dealerHeaders}
        rowLabelPrefix=""
      />
      <StrategyTable
        title="Soft totals"
        data={soft}
        dealerHeaders={dealerHeaders}
        rowLabelPrefix=""
      />
      <StrategyTable
        title="Paires"
        data={pairs}
        dealerHeaders={dealerHeaders}
        rowLabelPrefix="-"
        isPairs
      />
    </div>
  );
}

export default StrategyTables;
