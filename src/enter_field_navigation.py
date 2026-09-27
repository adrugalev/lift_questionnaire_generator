"""Move focus to the next visible questionnaire field after Enter."""

from __future__ import annotations

import streamlit as st


ENTER_FIELD_NAVIGATION_COMPONENT = st.components.v2.component(
    "enter_field_navigation",
    html='<span data-enter-field-navigation hidden></span>',
    js="""
    export default function(component) {
      const marker = component.parentElement.querySelector('[data-enter-field-navigation]');
      if (!marker) return;
      const doc = marker.ownerDocument;
      const win = doc.defaultView;
      const existing = win.__epssEnterFieldNavigation;
      if (existing?.version === 7) return;
      existing?.dispose?.();

      const selector = [
        '[data-testid="stTextInput"] input',
        '[data-testid="stNumberInput"] input',
        '[data-testid="stSelectbox"] input[role="combobox"]',
        '[data-testid="stDateInput"] [role="spinbutton"]',
        '[data-testid="stTextArea"] textarea',
        '[data-testid="stCheckbox"] input[type="checkbox"]',
      ].join(', ');
      let pending = null;
      let observer = null;
      let expiryTimer = null;
      let scheduled = false;
      let syntheticPointer = false;

      function fieldKey(element, main) {
        for (let node = element; node && node !== main; node = node.parentElement) {
          for (const name of node.classList ?? []) {
            if (name.startsWith('st-key-project_') || name.startsWith('st-key-group_')) {
              return name;
            }
          }
        }
        return null;
      }

      function visibleFields() {
        const main = doc.querySelector('[data-testid="stMain"]');
        if (!main) return [];
        const seen = new Set();
        const fields = [];
        for (const element of main.querySelectorAll(selector)) {
          const key = fieldKey(element, main);
          if (!key || seen.has(key) || element.disabled || !element.getClientRects().length) continue;
          if (element.closest('[aria-disabled="true"]')) continue;
          const box = element.getBoundingClientRect();
          fields.push({ element, key, top: box.top, left: box.left, order: fields.length });
          seen.add(key);
        }
        fields.sort((a, b) => {
          if (Math.abs(a.top - b.top) < 10) return a.left - b.left || a.order - b.order;
          return a.top - b.top;
        });
        return fields;
      }

      function nextField(sourceKey, fallbackKey) {
        const fields = visibleFields();
        const index = fields.findIndex(({ key }) => key === sourceKey);
        if (index >= 0) return fields[index + 1] ?? null;
        return fields.find(({ key }) => key === fallbackKey) ?? null;
      }

      function clearPending() {
        pending = null;
        observer?.disconnect();
        observer = null;
        win.clearTimeout(expiryTimer);
        expiryTimer = null;
      }

      function focusNext() {
        if (!pending) return;
        if (Date.now() >= pending.expires) {
          clearPending();
          return;
        }
        const next = nextField(pending.sourceKey, pending.fallbackKey);
        if (!next) return;
        if (pending.fromDate && !pending.clickedTarget) {
          syntheticPointer = true;
          next.element.dispatchEvent(new win.PointerEvent('pointerdown', {
            bubbles: true, cancelable: true, composed: true,
          }));
          next.element.dispatchEvent(new win.MouseEvent('mousedown', {
            bubbles: true, cancelable: true, composed: true,
          }));
          next.element.click();
          syntheticPointer = false;
          pending.clickedTarget = true;
        }
        if (doc.activeElement !== next.element) next.element.focus();
      }

      function scheduleFocus() {
        if (!pending || scheduled) return;
        scheduled = true;
        win.requestAnimationFrame(() => {
          scheduled = false;
          focusNext();
        });
      }

      function handleKeydown(event) {
        if (event.key !== 'Enter') {
          if (pending) clearPending();
          return;
        }
        if (event.repeat || event.isComposing || event.shiftKey || event.ctrlKey ||
            event.altKey || event.metaKey) return;
        const element = event.target;
        if (!(element instanceof win.HTMLElement) || element.tagName === 'TEXTAREA') return;
        const main = doc.querySelector('[data-testid="stMain"]');
        if (!main?.contains(element) || !element.matches(selector)) return;
        if (element.getAttribute('role') === 'combobox' &&
            element.getAttribute('aria-expanded') !== 'true') return;
        const sourceKey = fieldKey(element, main);
        if (!sourceKey) return;
        const next = nextField(sourceKey, null);
        if (!next) return;

        if (element.closest('[data-testid="stDateInput"]')) {
          event.preventDefault();
          event.stopPropagation();
        }

        clearPending();
        pending = {
          sourceKey,
          fallbackKey: next.key,
          fromDate: Boolean(element.closest('[data-testid="stDateInput"]')),
          clickedTarget: false,
          expires: Date.now() + 1600,
        };
        observer = new win.MutationObserver(scheduleFocus);
        observer.observe(doc.body, { childList: true, subtree: true });
        expiryTimer = win.setTimeout(clearPending, 1600);
        win.setTimeout(focusNext, 20);
        win.setTimeout(focusNext, 200);
      }

      function handlePointerDown() {
        if (pending && !syntheticPointer) clearPending();
      }

      doc.addEventListener('keydown', handleKeydown, true);
      doc.addEventListener('pointerdown', handlePointerDown, true);
      win.__epssEnterFieldNavigation = {
        version: 7,
        dispose() {
          clearPending();
          doc.removeEventListener('keydown', handleKeydown, true);
          doc.removeEventListener('pointerdown', handlePointerDown, true);
        },
      };
    }
    """,
)
