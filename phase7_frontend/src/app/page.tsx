"use client";

import { useState } from "react";
import styles from "./page.module.css";

type Recommendation = {
  rank: number;
  restaurant_name: string;
  location?: string;
  cuisines?: string;
  cost_for_two?: number;
  rating?: number;
  tags?: string;
  llm_reason: string;
  llm_summary: string;
};

type ResponseData = {
  success: boolean;
  recommendations: Recommendation[];
  warnings: string[];
  errors: string[];
};

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ResponseData | null>(null);
  
  const [form, setForm] = useState({
    location: "Bellandur",
    budget: "high",
    minimum_rating: "4.0",
    cuisine: ""
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setData(null);

    try {
      const payload = {
        location: form.location,
        budget: form.budget,
        cuisine: form.cuisine || null,
        minimum_rating: form.minimum_rating ? parseFloat(form.minimum_rating) : null,
        top_n: 5,
        mock: false
      };

      const res = await fetch("http://localhost:8000/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const result = await res.json();
      setData(result);
    } catch (error) {
      console.error(error);
      alert("Failed to connect to backend. Is the FastAPI server running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>Zomato AI</h1>
        <p className={styles.subtitle}>Discover your next favorite meal using LLM-powered recommendations.</p>
      </header>

      <div className={styles.glassPanel}>
        <form onSubmit={handleSubmit}>
          <div className={styles.formGrid}>
            <div className={styles.inputGroup}>
              <label>Location</label>
              <input 
                type="text" 
                name="location" 
                value={form.location} 
                onChange={handleChange} 
                className={styles.input} 
                required 
                placeholder="e.g. Bellandur"
              />
            </div>
            <div className={styles.inputGroup}>
              <label>Budget</label>
              <select 
                name="budget" 
                value={form.budget} 
                onChange={handleChange} 
                className={styles.input}
              >
                <option value="low">Low (₹0 - ₹800)</option>
                <option value="medium">Medium (₹500 - ₹1800)</option>
                <option value="high">High (₹1500+)</option>
              </select>
            </div>
            <div className={styles.inputGroup}>
              <label>Min Rating (0-5)</label>
              <input 
                type="number" 
                step="0.1" 
                min="0" 
                max="5"
                name="minimum_rating" 
                value={form.minimum_rating} 
                onChange={handleChange} 
                className={styles.input} 
              />
            </div>
            <div className={styles.inputGroup}>
              <label>Cuisine (Optional)</label>
              <input 
                type="text" 
                name="cuisine" 
                value={form.cuisine} 
                onChange={handleChange} 
                className={styles.input} 
                placeholder="e.g. Italian"
              />
            </div>
          </div>
          <button type="submit" className={styles.submitBtn} disabled={loading}>
            {loading ? "Analyzing Preferences..." : "Generate AI Recommendations"}
          </button>
        </form>
      </div>

      {loading && (
        <div className={styles.loaderContainer}>
          <div className={styles.spinner}></div>
          <p>Consulting with Llama 3.3...</p>
        </div>
      )}

      {data && data.success && data.recommendations.length > 0 && (
        <div className={styles.resultsArea}>
          <div className={styles.resultsHeader}>
            <div className={styles.llmSummary}>
              ✨ {data.recommendations[0].llm_summary}
            </div>
          </div>

          <div className={styles.grid}>
            {data.recommendations.map((rec) => (
              <div key={rec.rank} className={styles.card}>
                <img 
                  src="/images/placeholder.png" 
                  alt={rec.restaurant_name} 
                  className={styles.cardImage} 
                />
                <div className={styles.cardContent}>
                  <div className={styles.cardTop}>
                    <h3 className={styles.restName}>{rec.restaurant_name}</h3>
                    <div className={styles.rankBadge}>#{rec.rank}</div>
                  </div>
                  
                  <div className={styles.meta}>
                    <span className={styles.rating}>★ {rec.rating}</span>
                    <span>₹{rec.cost_for_two} for two</span>
                  </div>
                  
                  <p style={{color: '#a0a0ab', fontSize: '0.85rem', marginBottom: '1rem'}}>
                    {rec.cuisines}
                  </p>

                  <div className={styles.reasonBox}>
                    <strong>AI Insight:</strong> {rec.llm_reason}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data && data.errors && data.errors.length > 0 && (
        <div className={styles.resultsArea} style={{color: '#ff4757'}}>
          <h3>Oops! Something went wrong:</h3>
          <ul>
            {data.errors.map((err, i) => <li key={i}>{err}</li>)}
          </ul>
        </div>
      )}
    </main>
  );
}
