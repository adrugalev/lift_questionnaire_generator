"""Live shaft dimensions over a generated cutaway illustration."""

from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Any, Mapping

import streamlit as st


SHAFT_DIAGRAM_COMPONENT = st.components.v2.component(
    "shaft_diagram",
    html='<div data-shaft-diagram-root></div>',
    js="""
    export default function(component) {
      const root = component.parentElement.querySelector('[data-shaft-diagram-root]');
      if (!root) return;
      root.innerHTML = component.data?.markup ?? '';
      const card = root.querySelector('.shaft-card');
      if (!card) return;

      const regions = [
        { field: 'shaft_width_mm', label: 'Ширина шахты, мм', region: 'width' },
        { field: 'shaft_depth_mm', label: 'Глубина шахты, мм', region: 'depth' },
        { field: 'overhead_mm', label: 'Высота верхнего этажа, мм', region: 'overhead' },
        { field: 'pit_depth_mm', label: 'Глубина приямка, мм', region: 'pit' },
      ];
      for (const { field, label, region } of regions) {
        const show = () => { card.dataset.highlight = region; };
        const hide = () => {
          if (card.dataset.highlight === region) delete card.dataset.highlight;
        };
        const badge = card.querySelector(`[data-field="${field}"]`);
        if (badge) {
          badge.onmouseenter = show;
          badge.onmouseleave = hide;
          badge.onfocus = show;
          badge.onblur = hide;
        }
        const diagramArea = card.querySelector(`[data-shaft-hover="${region}"]`);
        if (diagramArea) {
          diagramArea.onmouseenter = show;
          diagramArea.onmouseleave = hide;
        }
        const input = root.ownerDocument.querySelector(`input[aria-label="${label}"]`);
        if (input) {
          input.onmouseenter = show;
          input.onmouseleave = hide;
          input.onfocus = show;
          input.onblur = hide;
        }
      }
    }
    """,
)

_ILLUSTRATION = Path(__file__).resolve().parents[1] / "templates" / "Shaft_photo" / "shaft_cutaway.webp"
_WINCH = Path(__file__).resolve().parents[1] / "templates" / "Shaft_photo" / "traction_winch.png"


@lru_cache(maxsize=1)
def _illustration_data_url() -> str:
    return "data:image/webp;base64," + b64encode(_ILLUSTRATION.read_bytes()).decode("ascii")


@lru_cache(maxsize=1)
def _winch_data_url() -> str:
    return "data:image/png;base64," + b64encode(_WINCH.read_bytes()).decode("ascii")


def _dimension(value: Any) -> str:
    raw = str(value).strip() if value is not None else ""
    if not raw:
        return "—"
    numeric = raw.replace(" ", "").replace(",", ".").replace(".", "", 1).isdigit()
    return escape(f"{raw} мм" if numeric else raw, quote=True)


def shaft_diagram_html(group: Mapping[str, Any]) -> str:
    """Return the cutaway with the four dimensions that help read it."""
    width = _dimension(group.get("shaft_width_mm"))
    depth = _dimension(group.get("shaft_depth_mm"))
    pit = _dimension(group.get("pit_depth_mm"))
    overhead = _dimension(group.get("overhead_mm"))
    illustration = _illustration_data_url()
    winch = _winch_data_url()

    return f"""
<style>
  .shaft-card {{
    background: linear-gradient(155deg, #fff 0%, #f4f8fd 100%);
    border: 1px solid #d9e5f2;
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(40, 81, 132, .08);
    box-sizing: border-box;
    color: #233d5b;
    font-family: inherit;
    margin: 0;
    overflow: hidden;
    padding: 14px 15px 9px;
  }}
  .shaft-card figcaption {{
    font-size: 17px;
    font-weight: 750;
    letter-spacing: -.02em;
    line-height: 1.2;
    margin: 0 0 3px;
  }}
  .shaft-caption-note {{
    color: #7388a1;
    font-size: 10px;
    line-height: 1.3;
  }}
  .shaft-stage {{
    position: relative;
    margin-top: 3px;
    isolation: isolate;
  }}
  .shaft-stage::before {{
    position: absolute;
    inset: 6% 3% 5%;
    background: radial-gradient(ellipse, #e6f0fa 0%, rgba(230, 240, 250, 0) 68%);
    content: "";
    z-index: -1;
  }}
  .shaft-art {{
    display: block;
    height: auto;
    width: 100%;
  }}
  .shaft-winch {{
    position: absolute;
    left: 41%;
    top: 9%;
    width: 18%;
    height: auto;
    pointer-events: none;
    filter: saturate(.72) brightness(1.05) drop-shadow(0 3px 4px rgba(31, 58, 83, .25));
  }}
  .shaft-measure-arrows {{
    position: absolute;
    inset: 0;
    height: 100%;
    width: 100%;
    overflow: visible;
    pointer-events: none;
  }}
  .shaft-measure-arrows .shaft-hit-area {{
    fill: transparent;
    pointer-events: all;
    cursor: pointer;
  }}
  .shaft-measure-arrows .shaft-hit-line {{
    fill: none;
    stroke: transparent;
    stroke-width: 60;
    stroke-linecap: round;
    pointer-events: stroke;
    cursor: pointer;
  }}
  .shaft-measure-arrows .shaft-arrow-halo {{
    fill: none;
    stroke: rgba(255, 255, 255, .95);
    stroke-linecap: round;
    stroke-width: 10;
    transition: stroke 180ms ease, stroke-width 180ms ease;
  }}
  .shaft-measure-arrows .shaft-arrow-width,
  .shaft-measure-arrows .shaft-arrow-depth {{
    fill: none;
    stroke-linecap: round;
    stroke-width: 5;
    transition: stroke 180ms ease, stroke-width 180ms ease, filter 180ms ease;
  }}
  .shaft-measure-arrows .shaft-arrow-width {{stroke: #2468b8;}}
  .shaft-measure-arrows .shaft-arrow-depth {{stroke: #604978;}}
  .shaft-card[data-highlight="width"] .shaft-arrow-halo-width {{
    stroke: rgba(133, 187, 255, .78);
    stroke-width: 19;
  }}
  .shaft-card[data-highlight="width"] .shaft-arrow-width {{
    stroke: #075fcb;
    stroke-width: 9;
    filter: drop-shadow(0 0 7px rgba(28, 111, 218, .85));
  }}
  .shaft-card[data-highlight="width"] #shaft-width-tip path {{fill: #075fcb;}}
  .shaft-card[data-highlight="depth"] .shaft-arrow-halo-depth {{
    stroke: rgba(151, 128, 174, .6);
    stroke-width: 19;
  }}
  .shaft-card[data-highlight="depth"] .shaft-arrow-depth {{
    stroke: #503867;
    stroke-width: 9;
    filter: drop-shadow(0 0 5px rgba(81, 57, 106, .55));
  }}
  .shaft-card[data-highlight="depth"] #shaft-depth-tip path {{fill: #503867;}}
  .shaft-region {{
    opacity: 0;
    transition: opacity 180ms ease;
  }}
  .shaft-region .shaft-face {{
    stroke: none;
  }}
  .shaft-region--overhead .shaft-face--left {{fill: #84e4dd; fill-opacity: .26;}}
  .shaft-region--overhead .shaft-face--back {{fill: #41d2cc; fill-opacity: .34;}}
  .shaft-region--overhead .shaft-face--floor {{fill: #a5eee8; fill-opacity: .4;}}
  .shaft-region--pit .shaft-face--left {{fill: #ffe2a0; fill-opacity: .32;}}
  .shaft-region--pit .shaft-face--back {{fill: #f5b84d; fill-opacity: .28;}}
  .shaft-region--pit .shaft-face--floor {{fill: #ffc75c; fill-opacity: .46;}}
  .shaft-region .shaft-region-outline {{
    fill: none;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 4;
  }}
  .shaft-region--overhead .shaft-region-outline {{stroke: #139fa4;}}
  .shaft-region--pit .shaft-region-outline {{stroke: #d99a27;}}
  .shaft-region .shaft-region-corner {{
    fill: none;
    stroke-width: 2.5;
    stroke-linecap: round;
    stroke-linejoin: round;
  }}
  .shaft-region--overhead .shaft-region-corner {{stroke: #139fa4; stroke-opacity: .45;}}
  .shaft-region--pit .shaft-region-corner {{stroke: #d99a27; stroke-opacity: .5;}}
  .shaft-card[data-highlight="overhead"] .shaft-region--overhead,
  .shaft-card[data-highlight="pit"] .shaft-region--pit {{
    opacity: 1;
  }}
  .shaft-dim {{
    position: absolute;
    box-sizing: border-box;
    min-width: 98px;
    max-width: 44%;
    padding: 6px 8px 5px;
    background: rgba(255, 255, 255, .96);
    border: 1px solid #c5d9ef;
    border-left: 3px solid #2468b8;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(43, 83, 128, .1);
  }}
  .shaft-dim-label {{
    display: block;
    color: #6b83a0;
    font-size: 11px;
    font-weight: 750;
    line-height: 1.15;
  }}
  .shaft-dim-value {{
    display: block;
    color: #1e5fa8;
    font-size: 15px;
    font-weight: 800;
    line-height: 1.15;
    margin-top: 3px;
    white-space: nowrap;
  }}
  .shaft-dim--width,
  .shaft-dim--depth,
  .shaft-dim--overhead,
  .shaft-dim--pit {{
    cursor: pointer;
    transition: background 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
  }}
  .shaft-card[data-highlight="overhead"] .shaft-dim--overhead {{
    background: #e8fbf9;
    border-color: #49bdb9;
    border-left-color: #139fa4;
    box-shadow: 0 5px 18px rgba(28, 157, 160, .22);
  }}
  .shaft-card[data-highlight="pit"] .shaft-dim--pit {{
    background: #fff5e5;
    border-color: #e5a345;
    border-left-color: #d99a27;
    box-shadow: 0 5px 18px rgba(209, 139, 32, .2);
  }}
  .shaft-card[data-highlight="width"] .shaft-dim--width {{
    background: #eaf3ff;
    border-color: #4d91e7;
    border-left-color: #2468b8;
    box-shadow: 0 5px 18px rgba(33, 109, 205, .24);
  }}
  .shaft-card[data-highlight="depth"] .shaft-dim--depth {{
    background: #f4f1f7;
    border-color: #b9adca;
    border-left-color: #604978;
    box-shadow: 0 5px 16px rgba(77, 57, 101, .17);
  }}
  .shaft-dim--width {{left: -2%; top: 40%;}}
  .shaft-dim--overhead {{left: 1%; top: 3%; border-left-color: #139fa4;}}
  .shaft-dim--depth {{right: -1%; top: 54%; border-left-color: #604978;}}
  .shaft-dim--pit {{right: 1%; bottom: 8%; border-left-color: #d99a27;}}
  @media (max-width: 280px) {{
    .shaft-card {{padding: 12px 10px 8px;}}
    .shaft-dim {{min-width: 74px; padding: 5px 6px 4px;}}
    .shaft-dim-label {{font-size: 9px;}}
    .shaft-dim-value {{font-size: 13px;}}
  }}
</style>
<figure class="shaft-card" aria-label="Схема шахты лифта">
  <figcaption>Шахта в разрезе</figcaption>
  <div class="shaft-caption-note">Схематично · не в масштабе</div>
  <div class="shaft-stage">
    <img class="shaft-art" src="{illustration}" alt="Технический разрез лифтовой шахты с лебёдкой, кабиной и приямком">
    <img class="shaft-winch" src="{winch}" alt="" aria-hidden="true">
    <svg class="shaft-measure-arrows" viewBox="0 0 1024 1536" aria-hidden="true">
      <!-- Facets are traced to the perspective edges of shaft_cutaway.webp. -->
      <g class="shaft-region shaft-region--overhead">
        <path class="shaft-face shaft-face--left" d="M393 94 465 59 465 338 389 379Z"/>
        <path class="shaft-face shaft-face--back" d="M465 59 623 90 623 382 465 338Z"/>
        <path class="shaft-face shaft-face--floor" d="M389 379 465 338 623 382 550 420Z"/>
        <path class="shaft-region-outline" d="M389 379 393 94 465 59 623 90V382"/>
        <path class="shaft-region-corner" d="M465 59V338M389 379 465 338 623 382 550 420 389 379"/>
      </g>
      <g class="shaft-region shaft-region--pit">
        <path class="shaft-face shaft-face--left" d="M372 1249 471 1187 471 1290 372 1353Z"/>
        <path class="shaft-face shaft-face--back" d="M471 1187 670 1285 670 1394 471 1290Z"/>
        <path class="shaft-face shaft-face--floor" d="M372 1353 471 1290 670 1394 579 1478Z"/>
        <path class="shaft-region-outline" d="M372 1249 471 1187 670 1285 670 1394 579 1478 372 1353Z"/>
      </g>
      <defs>
        <marker id="shaft-width-tip" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 12 6 0 12Z" fill="#2468b8" stroke="#fff" stroke-width="1.5"/></marker>
        <marker id="shaft-depth-tip" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 12 6 0 12Z" fill="#604978" stroke="#fff" stroke-width="1.5"/></marker>
      </defs>
      <path class="shaft-arrow-halo shaft-arrow-halo-width" d="M380 705 618 780"/>
      <path class="shaft-arrow-halo shaft-arrow-halo-depth" d="M500 1016 675 916"/>
      <path class="shaft-arrow-width" d="M380 705 618 780" marker-start="url(#shaft-width-tip)" marker-end="url(#shaft-width-tip)"/>
      <path class="shaft-arrow-depth" d="M500 1016 675 916" marker-start="url(#shaft-depth-tip)" marker-end="url(#shaft-depth-tip)"/>
      <path class="shaft-hit-area" data-shaft-hover="overhead" d="M393 94 465 59 623 90 623 382 550 420 389 379Z"/>
      <path class="shaft-hit-area" data-shaft-hover="pit" d="M372 1249 471 1187 670 1285 670 1394 579 1478 372 1353Z"/>
      <path class="shaft-hit-line" data-shaft-hover="width" d="M380 705 618 780"/>
      <path class="shaft-hit-line" data-shaft-hover="depth" d="M500 1016 675 916"/>
    </svg>
    <div class="shaft-dim shaft-dim--width" data-field="shaft_width_mm" tabindex="0"><span class="shaft-dim-label">Ширина шахты</span><strong class="shaft-dim-value">{width}</strong></div>
    <div class="shaft-dim shaft-dim--overhead" data-field="overhead_mm" tabindex="0"><span class="shaft-dim-label">Верхний этаж</span><strong class="shaft-dim-value">{overhead}</strong></div>
    <div class="shaft-dim shaft-dim--depth" data-field="shaft_depth_mm" tabindex="0"><span class="shaft-dim-label">Глубина шахты</span><strong class="shaft-dim-value">{depth}</strong></div>
    <div class="shaft-dim shaft-dim--pit" data-field="pit_depth_mm" tabindex="0"><span class="shaft-dim-label">Приямок</span><strong class="shaft-dim-value">{pit}</strong></div>
  </div>
</figure>
"""
