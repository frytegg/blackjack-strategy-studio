// frontend/src/components/RulesForm.jsx

import React, { useState } from "react";

const defaultConfig = {
  num_decks: 6,
  csm: false,
  dealer_hits_soft_17: false,
  european_no_hole_card: false,
  allow_split_aces: true,
  allow_resplit_aces: false,
  allow_double_after_split: true,
  allow_surrender: false,
  surrender_allowed_vs_ace: false,
  one_card_only_after_split_aces: true
};

function RulesForm({ onGenerate, onDownloadPdf, loading, pdfLoading }) {
  const [config, setConfig] = useState(defaultConfig);

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : Number(value)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(config);
  };

  const handleDownload = (e) => {
    e.preventDefault();
    onDownloadPdf(config);
  };

  return (
    <form className="rules-form" onSubmit={handleSubmit}>
      <h2>Configuration des règles</h2>

      <div className="rules-grid">
        <div className="rules-field">
          <label htmlFor="num_decks">Nombre de paquets</label>
          <select
            id="num_decks"
            name="num_decks"
            value={config.num_decks}
            onChange={handleChange}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={4}>4</option>
            <option value={6}>6</option>
            <option value={8}>8</option>
          </select>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="csm"
              checked={config.csm}
              onChange={handleChange}
            />
            CSM (Continuous Shuffling Machine)
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="dealer_hits_soft_17"
              checked={config.dealer_hits_soft_17}
              onChange={handleChange}
            />
            Croupier tire sur soft 17 (H17)
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="european_no_hole_card"
              checked={config.european_no_hole_card}
              onChange={handleChange}
            />
            Variante européenne (ENHC, pas de hole card)
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="allow_split_aces"
              checked={config.allow_split_aces}
              onChange={handleChange}
            />
            Split des As autorisé
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="allow_resplit_aces"
              checked={config.allow_resplit_aces}
              onChange={handleChange}
            />
            Re-split des As autorisé (approximé)
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="allow_double_after_split"
              checked={config.allow_double_after_split}
              onChange={handleChange}
            />
            Double après split autorisé (DAS)
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="allow_surrender"
              checked={config.allow_surrender}
              onChange={handleChange}
            />
            Surrender (abandon) autorisé
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="surrender_allowed_vs_ace"
              checked={config.surrender_allowed_vs_ace}
              onChange={handleChange}
            />
            Surrender autorisé contre As
          </label>
        </div>

        <div className="rules-field rules-field-checkbox">
          <label>
            <input
              type="checkbox"
              name="one_card_only_after_split_aces"
              checked={config.one_card_only_after_split_aces}
              onChange={handleChange}
            />
            Une seule carte après split des As
          </label>
        </div>
      </div>

      <div className="rules-actions">
        <button type="submit" disabled={loading}>
          {loading ? "Génération..." : "Générer le tableau"}
        </button>
        <button
          type="button"
          onClick={handleDownload}
          disabled={pdfLoading}
        >
          {pdfLoading ? "Génération du PDF..." : "Télécharger en PDF"}
        </button>
      </div>
    </form>
  );
}

export default RulesForm;
