// frontend/src/App.jsx

import React, { useState } from "react";
import RulesForm from "./components/RulesForm";
import StrategyTables from "./components/StrategyTables";
import Legend from "./components/Legend";
import { fetchStrategy, downloadStrategyPdf } from "./api/strategyApi";

function App() {
  const [rules, setRules] = useState(null);
  const [strategy, setStrategy] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async (config) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchStrategy(config);
      setStrategy(data);
      setRules(data.rules || config);
    } catch (e) {
      console.error(e);
      setError("Erreur lors de la génération de la stratégie.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (config) => {
    setPdfLoading(true);
    setError(null);
    try {
      const blob = await downloadStrategyPdf(config);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "blackjack_strategy.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      setError("Erreur lors de la génération du PDF.");
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Générateur de basic strategy Blackjack</h1>
        <p className="app-subtitle">
          Configure les règles, génère les tableaux et télécharge-les en PDF.
        </p>
      </header>

      <main className="app-main">
        <section className="app-section app-section-form">
          <RulesForm
            onGenerate={handleGenerate}
            onDownloadPdf={handleDownloadPdf}
            loading={loading}
            pdfLoading={pdfLoading}
          />
        </section>

        <section className="app-section app-section-tables">
          <Legend />
          {error && <div className="app-error">{error}</div>}
          {loading && <div className="app-loading">Calcul de la stratégie...</div>}
          {strategy && !loading && (
            <StrategyTables strategy={strategy} />
          )}
          {!strategy && !loading && (
            <div className="app-placeholder">
              Configure les règles puis clique sur « Générer le tableau ».
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
