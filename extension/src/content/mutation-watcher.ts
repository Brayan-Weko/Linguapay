/**
 * MutationWatcher — Détection temps réel du contenu inédit (debounce 80 ms)
 * avec verrou anti-boucle infinie lors des écritures DOM de LinguaPay.
 */

import { SHADOW_HOST_ID } from "./shadow-overlay";

export const OBSERVER_DEBOUNCE_MS = 80;

export class MutationWatcher {
  private observer: MutationObserver | null = null;
  private timer: number | null = null;
  private paused = false;
  private pendingRoots = new Set<Node>();

  constructor(private readonly onMutations: (roots: Node[]) => void) {}

  start(target: Node = document.body): void {
    if (this.observer || !target) return;
    this.observer = new MutationObserver((mutations) => {
      if (this.paused) return;
      let relevant = false;
      for (const m of mutations) {
        if (m.target instanceof Element && m.target.id === SHADOW_HOST_ID) continue;
        if (m.type === "childList" && m.addedNodes.length > 0) {
          m.addedNodes.forEach((n) => {
            if (n instanceof Element && n.id === SHADOW_HOST_ID) return;
            this.pendingRoots.add(n);
            relevant = true;
          });
        } else if (m.type === "characterData" && m.target.parentElement) {
          this.pendingRoots.add(m.target.parentElement);
          relevant = true;
        }
      }
      if (relevant) {
        this.scheduleFlush();
      }
    });

    this.observer.observe(target, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  stop(): void {
    if (this.timer !== null) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
    this.observer?.disconnect();
    this.observer = null;
    this.pendingRoots.clear();
  }

  runMuted(fn: () => void): void {
    this.paused = true;
    try {
      fn();
    } finally {
      // Microtask delay ensures synchronous DOM mutations settle before resuming
      queueMicrotask(() => {
        this.paused = false;
      });
    }
  }

  private scheduleFlush(): void {
    if (this.timer !== null) {
      window.clearTimeout(this.timer);
    }
    this.timer = window.setTimeout(() => {
      this.timer = null;
      const roots = Array.from(this.pendingRoots);
      this.pendingRoots.clear();
      if (roots.length > 0 && !this.paused) {
        this.onMutations(roots);
      }
    }, OBSERVER_DEBOUNCE_MS);
  }
}
