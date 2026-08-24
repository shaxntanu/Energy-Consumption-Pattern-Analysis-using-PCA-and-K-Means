'use client';

import React, { useEffect, useRef, useState } from 'react';

interface Card {
  id: number;
  title: string;
  icon: string;
  description: string;
  details: string[];
  color: string;
}

const NARRATIVE_CARDS: Card[] = [
  {
    id: 1,
    title: 'The Question',
    icon: '❓',
    description: 'Can energy consumption patterns reveal something meaningful about how we use electricity?',
    details: [
      'Energy data is time series — each consumer has 24 readings per day',
      'Patterns recur: weekday, weekend, seasonal shifts',
      'Question: Are there distinct types of daily profiles?'
    ],
    color: '#3BC9DE'
  },
  {
    id: 2,
    title: 'Dimensionality Reduction',
    icon: '📉',
    description: 'PCA compresses 51 correlated features into 14 uncorrelated components.',
    details: [
      'Standardize features to zero mean, unit variance',
      'PCA projects data onto directions of maximum variance',
      'Keep components that explain 95% of total variance',
      'Reduces noise, reveals signal'
    ],
    color: '#F5A524'
  },
  {
    id: 3,
    title: 'Clustering',
    icon: '🎯',
    description: 'K-Means finds groups in the compressed space using a pre-registered selection rule.',
    details: [
      'Try K = 2, 3, 4, ... 10 (search)',
      'For each K, compute silhouette, calinski, davies-bouldin, gap',
      'Combine metrics into a single score',
      'Pick K that maximizes the score'
    ],
    color: '#B085F5'
  },
  {
    id: 4,
    title: 'Discovery',
    icon: '✨',
    description: 'Three distinct daily rhythms emerge, each sensible in real-world terms.',
    details: [
      'Midday-Peaking: peaks during afternoon work hours',
      'Flat All-Day: steady, minimal variation throughout day',
      'Evening-Peaking: rises sharply after dark, driven by heating/cooking'
    ],
    color: '#3BC9DE'
  }
];

export default function NarrativeCards() {
  const [visibleCards, setVisibleCards] = useState<Set<number>>(new Set());
  const cardRefsRef = useRef<Map<number, HTMLDivElement>>(new Map());

  useEffect(() => {
    const observers = NARRATIVE_CARDS.map((card) => {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setVisibleCards((prev) => new Set([...prev, card.id]));
          }
        },
        { threshold: 0.2 }
      );

      const element = cardRefsRef.current.get(card.id);
      if (element) {
        observer.observe(element);
      }

      return observer;
    });

    return () => {
      observers.forEach((observer) => observer.disconnect());
    };
  }, []);

  return (
    <div className="w-full">
      <div className="space-y-6">
        {NARRATIVE_CARDS.map((card, index) => (
          <div
            key={card.id}
            ref={(el) => {
              if (el) cardRefsRef.current.set(card.id, el);
            }}
            className={`bg-[#141A24] border border-[#262E3D] rounded-lg overflow-hidden transition-all duration-700 ${
              visibleCards.has(card.id)
                ? 'opacity-100 translate-y-0'
                : 'opacity-0 translate-y-8'
            }`}
            style={{
              transitionDelay: `${index * 100}ms`
            }}
          >
            {/* Header with icon */}
            <div className="flex items-start gap-4 p-6 border-b border-[#262E3D]">
              <div
                className="w-16 h-16 rounded-lg flex items-center justify-center text-2xl flex-shrink-0"
                style={{
                  backgroundColor: card.color,
                  opacity: 0.1,
                  borderLeft: `3px solid ${card.color}`
                }}
              >
                {card.icon}
              </div>
              <div className="flex-1">
                <p
                  className="text-xs font-mono font-semibold uppercase tracking-widest mb-2"
                  style={{ color: card.color }}
                >
                  {card.title}
                </p>
                <h3 className="text-lg font-semibold text-[#EAECEF] leading-tight">
                  {card.description}
                </h3>
              </div>
            </div>

            {/* Details */}
            <div className="p-6">
              <ul className="space-y-3">
                {card.details.map((detail, i) => (
                  <li key={i} className="flex gap-3 text-sm text-[#8A93A6]">
                    <span className="text-[#3BC9DE] font-semibold flex-shrink-0">•</span>
                    <span>{detail}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-12 bg-gradient-to-r from-[#141A24] to-[#1a212e] border border-[#262E3D] rounded-lg p-8">
        <p className="text-xs font-mono text-[#3BC9DE] uppercase tracking-widest mb-4">
          The Result
        </p>
        <h3 className="text-2xl font-semibold text-[#EAECEF] mb-4">
          A interpretable, rule-driven clustering reveals three types of energy consumers
        </h3>
        <p className="text-[#8A93A6] leading-relaxed">
          Starting from high-dimensional data, dimensionality reduction + pre-registered selection yields clusters that are both statistically sound and intuitively meaningful. Each cluster tells a story about how its members use energy.
        </p>
      </div>
    </div>
  );
}
