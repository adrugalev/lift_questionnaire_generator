"""Interactive top-view selector for cabin handrail walls."""

from __future__ import annotations

import streamlit as st


HANDRAIL_WALL_PICKER = st.components.v2.component(
    "handrail_wall_picker",
    html="""
    <div class="wall-picker" data-handrail-wall-picker>
      <div class="picker-heading">
        <span class="picker-title">Расположение поручней</span>
        <span class="picker-hint">Выберите нужные стены (можно несколько).</span>
      </div>
      <svg class="cabin-diagram" viewBox="0 0 360 282"
           role="group" aria-label="Схема кабины сверху. Вход внизу.">
        <rect class="diagram-background" x="28" y="10" width="304" height="262" rx="18" />
        <rect class="cabin-floor" x="94" y="48" width="172" height="158" rx="3" />
        <path class="floor-detail" d="M112 64h136v126H112z" />
        <text class="floor-label" x="180" y="132" text-anchor="middle">КАБИНА</text>

        <g class="wall" data-wall="left" role="button" tabindex="0"
           aria-label="Левая стена" aria-pressed="false">
          <polygon class="wall-surface" points="60,30 94,48 94,206 60,235" />
          <path class="rail-line" d="M77 79v111" />
          <text class="wall-symbol" x="77" y="119" text-anchor="middle">＋</text>
        </g>
        <g class="wall" data-wall="right" role="button" tabindex="0"
           aria-label="Правая стена" aria-pressed="false">
          <polygon class="wall-surface" points="266,48 300,30 300,235 266,206" />
          <path class="rail-line" d="M283 79v111" />
          <text class="wall-symbol" x="283" y="119" text-anchor="middle">＋</text>
        </g>
        <g class="wall rear-wall" data-wall="rear" role="button" tabindex="0"
           aria-label="Задняя стена" aria-pressed="false">
          <polygon class="wall-surface" points="60,30 300,30 266,48 94,48" />
          <path class="rail-line" d="M119 39h122" />
          <path class="wall-symbol rear-wall-symbol" d="M180 34v10m-5-5h10" />
          <rect class="rear-wall-hit-area" x="95" y="24" width="170" height="38" />
        </g>

        <g class="rear-door" aria-hidden="true">
          <path class="fixed-wall" d="M60 30h61M239 30h61" />
          <g class="center-opening">
            <rect class="door-panel" x="121" y="25" width="59" height="10" rx="1.5" />
            <rect class="door-panel" x="180" y="25" width="59" height="10" rx="1.5" />
            <path class="door-seam" d="M180 26v8" />
          </g>
          <g class="telescopic-opening">
            <rect class="door-panel" x="121" y="25" width="63" height="5" rx="1" />
            <rect class="door-panel" x="177" y="31" width="62" height="5" rx="1" />
          </g>
        </g>

        <path class="entrance-side" d="M60 235h61M239 235h61" />
        <g class="center-opening" aria-hidden="true">
          <rect class="door-panel" x="121" y="230" width="59" height="10" rx="1.5" />
          <rect class="door-panel" x="180" y="230" width="59" height="10" rx="1.5" />
          <path class="door-seam" d="M180 231v8" />
        </g>
        <g class="telescopic-opening" aria-hidden="true">
          <rect class="door-panel" x="121" y="230" width="63" height="5" rx="1" />
          <rect class="door-panel" x="177" y="236" width="62" height="5" rx="1" />
        </g>
        <path class="entry-arrow" d="M180 268v-22m-7 7 7-7 7 7" />
      </svg>
      <div class="picker-summary" data-summary aria-live="polite">Стены не выбраны</div>
    </div>
    """,
    css="""
    .wall-picker {
      box-sizing: border-box;
      width: 100%;
      max-width: 300px;
      margin: 0 auto;
      padding: 9px 11px 8px;
      border: 1px solid #d9e3f0;
      border-radius: 12px;
      background: #f9fbff;
      color: #263648;
      font-family: "Source Sans Pro", Arial, sans-serif;
    }
    .picker-heading { display: grid; gap: 2px; text-align: center; }
    .picker-title { font-size: 14px; font-weight: 700; }
    .picker-hint { color: #66758a; font-size: 12px; line-height: 1.2; }
    .cabin-diagram { display: block; width: 100%; height: auto; margin: 4px auto 0; }
    .diagram-background { fill: #fff; stroke: #e4ebf4; }
    .cabin-floor { fill: #f0f6ff; stroke: #c5d5eb; stroke-width: 2; }
    .floor-detail { fill: none; stroke: #dbe7f5; stroke-width: 1.5; }
    .floor-label { fill: #98a8bd; font-size: 12px; font-weight: 700; letter-spacing: 2px; }
    .wall { cursor: pointer; outline: none; }
    .wall-surface {
      fill: #dce6f2;
      stroke: #9eb0c7;
      stroke-width: 2;
      transition: fill 140ms ease, stroke 140ms ease;
    }
    .wall:hover .wall-surface, .wall:focus-visible .wall-surface {
      fill: #b8d6ff;
      stroke: #3579d4;
      stroke-width: 3;
    }
    .wall.is-selected .wall-surface { fill: #2f67e8; stroke: #184eae; }
    .wall.is-selected:hover .wall-surface,
    .wall.is-selected:focus-visible .wall-surface { fill: #2459d0; }
    .rail-line {
      fill: none;
      stroke: #fff;
      stroke-width: 5;
      stroke-linecap: round;
      opacity: 0;
      pointer-events: none;
    }
    .wall.is-selected .rail-line { opacity: 1; }
    .wall-symbol {
      fill: #6b84a5;
      font-size: 27px;
      font-weight: 400;
      pointer-events: none;
    }
    .rear-wall-symbol {
      fill: none;
      stroke: #6b84a5;
      stroke-width: 1.8;
      stroke-linecap: round;
    }
    .rear-wall-hit-area { fill: transparent; }
    .wall.is-selected .wall-symbol { opacity: 0; }
    .rear-door { display: none; }
    .is-through .rear-wall { display: none; }
    .is-through .rear-door { display: block; }
    .telescopic-opening { display: none; }
    .is-telescopic .center-opening { display: none; }
    .is-telescopic .telescopic-opening { display: block; }
    .fixed-wall, .entrance-side {
      fill: none;
      stroke: #9eb0c7;
      stroke-width: 8;
      stroke-linecap: square;
    }
    .door-panel { fill: #e7edf5; stroke: #899cb3; stroke-width: 1.5; }
    .door-seam { fill: none; stroke: #98aac0; stroke-width: 1.5; }
    .telescopic-opening .door-panel {
      fill: #d4e6fb;
      stroke: #3d70b0;
      stroke-width: 1.8;
    }
    .telescopic-opening .door-panel:nth-of-type(2) { fill: #c4ddf8; }
    .entry-arrow { fill: none; stroke: #517bb6; stroke-width: 2; stroke-linecap: round; }
    .picker-summary {
      min-height: 17px;
      margin-top: 4px;
      color: #52647b;
      font-size: 12px;
      text-align: center;
    }
    @media (max-width: 300px) {
      .wall-picker { padding: 8px; }
    }
    """,
    js="""
    export default function(component) {
      const { data, parentElement, setStateValue } = component;
      const picker = parentElement.querySelector('[data-handrail-wall-picker]');
      if (!picker) return;

      const through = Boolean(data?.through);
      const order = through ? ['left', 'right'] : ['left', 'right', 'rear'];
      const names = { left: 'слева', right: 'справа', rear: 'сзади' };
      const selected = new Set(
        Array.isArray(data?.selected)
          ? data.selected.filter((wall) => order.includes(wall))
          : []
      );
      picker.classList.toggle('is-through', through);
      picker.classList.toggle('is-telescopic', Boolean(data?.telescopic));

      function paint() {
        for (const control of picker.querySelectorAll('[data-wall]')) {
          const active = selected.has(control.dataset.wall);
          control.classList.toggle('is-selected', active);
          control.setAttribute('aria-pressed', String(active));
        }
        const summary = picker.querySelector('[data-summary]');
        if (summary) {
          const walls = order.filter((wall) => selected.has(wall));
          summary.textContent = walls.length
            ? `Поручни: ${walls.map((wall) => names[wall]).join(', ')}`
            : 'Стены не выбраны';
        }
      }

      function toggle(wall) {
        if (!order.includes(wall)) return;
        if (selected.has(wall)) selected.delete(wall);
        else selected.add(wall);
        paint();
        setStateValue('walls', order.filter((item) => selected.has(item)));
      }

      for (const control of picker.querySelectorAll('[data-wall]')) {
        control.onclick = () => toggle(control.dataset.wall);
        if (control.tagName.toLowerCase() === 'g') {
          control.onkeydown = (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              toggle(control.dataset.wall);
            }
          };
        }
      }
      paint();
    }
    """,
)
