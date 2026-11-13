/**
 * DOMWalker — Traversée sécurisée du DOM avec exclusions strictes des champs secrets
 * et mémorisation non-destructive des textes originaux (restauration en 1 clic).
 */

import { SHADOW_HOST_ID } from "./shadow-overlay";

export const EXCLUDED_TAGS = new Set([
  "SCRIPT",
  "STYLE",
  "NOSCRIPT",
  "SVG",
  "CODE",
  "PRE",
  "TEXTAREA",
  "INPUT",
  "SELECT",
  "OPTION",
]);

export const SENSITIVE_INPUT_KEYWORDS = [
  "pin",
  "cvv",
  "cvc",
  "otp",
  "secret",
  "token",
  "password",
  "passcode",
];

export interface ScannedSegment {
  id: string;
  kind: "text" | "placeholder";
  node: Text | HTMLInputElement | HTMLTextAreaElement;
  leadingSpace: string;
  trailingSpace: string;
  originalTrimmed: string;
  criticality: string;
}

export function isSensitiveInput(el: Element): boolean {
  if (!(el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement)) {
    return false;
  }
  if (el instanceof HTMLInputElement) {
    const t = (el.type || "").toLowerCase();
    if (t === "password" || t === "hidden") return true;
  }
  const ac = (el.getAttribute("autocomplete") || "").toLowerCase();
  if (ac.startsWith("cc-") || ac === "one-time-code" || ac.includes("password")) {
    return true;
  }
  const fingerprint = `${el.id} ${el.name} ${el.className}`.toLowerCase();
  return SENSITIVE_INPUT_KEYWORDS.some((kw) => fingerprint.includes(kw));
}

function isInsideIgnoredSubtree(el: Element | null): boolean {
  let cur: Element | null = el;
  while (cur) {
    if (cur.id === SHADOW_HOST_ID || cur.hasAttribute("data-linguapay-ignore")) {
      return true;
    }
    cur = cur.parentElement;
  }
  return false;
}

function inferCriticality(el: Element | null): string {
  if (!el) return "UI_NAV";
  const role = (el.getAttribute("role") || "").toLowerCase();
  const cls = (el.className || "").toString().toLowerCase();
  if (role === "alert" || cls.includes("security") || cls.includes("danger") || cls.includes("error")) {
    return "CRITICAL_SECURITY";
  }
  if (cls.includes("balance") || cls.includes("fee") || cls.includes("modal") || cls.includes("dynamic")) {
    return "FINANCIAL_CORE";
  }
  return "UI_NAV";
}

export class DOMSnapshotManager {
  private originalTextMap = new WeakMap<Text, string>();
  private originalPlaceholderMap = new WeakMap<Element, string>();
  private trackedTextNodes = new Set<Text>();
  private trackedPlaceholders = new Set<HTMLInputElement | HTMLTextAreaElement>();
  private idCounter = 0;

  scan(root: Node = document.body): ScannedSegment[] {
    const segments: ScannedSegment[] = [];
    if (!root) return segments;

    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (EXCLUDED_TAGS.has(parent.tagName)) return NodeFilter.FILTER_REJECT;
        if (isInsideIgnoredSubtree(parent)) return NodeFilter.FILTER_REJECT;
        if (isSensitiveInput(parent)) return NodeFilter.FILTER_REJECT;
        const val = node.nodeValue ?? "";
        const trimmed = val.trim();
        if (trimmed.length < 2) return NodeFilter.FILTER_REJECT;
        // Skip already-translated exact text unless original changed externally
        if (parent.getAttribute("data-linguapay-translated") === "1" && this.originalTextMap.has(node as Text)) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });

    let current: Node | null;
    while ((current = walker.nextNode())) {
      const textNode = current as Text;
      const raw = textNode.nodeValue ?? "";
      const match = raw.match(/^(\s*)([\s\S]*?)(\s*)$/);
      const leadingSpace = match?.[1] ?? "";
      const trimmed = match?.[2] ?? raw.trim();
      const trailingSpace = match?.[3] ?? "";
      if (!trimmed) continue;

      if (!this.originalTextMap.has(textNode)) {
        this.originalTextMap.set(textNode, raw);
      }
      this.trackedTextNodes.add(textNode);

      this.idCounter += 1;
      segments.push({
        id: `dom_${this.idCounter}`,
        kind: "text",
        node: textNode,
        leadingSpace,
        trailingSpace,
        originalTrimmed: this.originalTextMap.get(textNode)?.trim() ?? trimmed,
        criticality: inferCriticality(textNode.parentElement),
      });
    }

    if (root instanceof Element || root === document.body) {
      const container = root as Element;
      const inputs = container.querySelectorAll("input[placeholder], textarea[placeholder]");
      inputs.forEach((el) => {
        if (
          !(el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) ||
          isInsideIgnoredSubtree(el) ||
          isSensitiveInput(el)
        ) {
          return;
        }
        if (el.getAttribute("data-linguapay-ph-translated") === "1" && this.originalPlaceholderMap.has(el)) {
          return;
        }
        const ph = el.placeholder;
        if (!ph || ph.trim().length < 2) return;
        if (!this.originalPlaceholderMap.has(el)) {
          this.originalPlaceholderMap.set(el, ph);
        }
        this.trackedPlaceholders.add(el);
        this.idCounter += 1;
        segments.push({
          id: `ph_${this.idCounter}`,
          kind: "placeholder",
          node: el,
          leadingSpace: "",
          trailingSpace: "",
          originalTrimmed: this.originalPlaceholderMap.get(el) ?? ph,
          criticality: "UI_NAV",
        });
      });
    }

    return segments;
  }

  applyTranslation(
    seg: ScannedSegment,
    translatedText: string,
    bilingualTooltip: boolean,
    tierBadge: string
  ): void {
    if (seg.kind === "text" && seg.node instanceof Text) {
      seg.node.nodeValue = `${seg.leadingSpace}${translatedText}${seg.trailingSpace}`;
      const parent = seg.node.parentElement;
      if (parent) {
        parent.setAttribute("data-linguapay-translated", "1");
        parent.setAttribute("data-linguapay-tier", tierBadge);
        if (bilingualTooltip) {
          parent.setAttribute("title", `[Original FR/EN] ${seg.originalTrimmed} (${tierBadge})`);
        } else {
          parent.removeAttribute("title");
        }
      }
    } else if (seg.kind === "placeholder" && (seg.node instanceof HTMLInputElement || seg.node instanceof HTMLTextAreaElement)) {
      seg.node.placeholder = translatedText;
      seg.node.setAttribute("data-linguapay-ph-translated", "1");
    }
  }

  restoreAll(): void {
    for (const node of this.trackedTextNodes) {
      const orig = this.originalTextMap.get(node);
      if (orig !== undefined && node.isConnected) {
        node.nodeValue = orig;
      }
      if (node.parentElement) {
        node.parentElement.removeAttribute("data-linguapay-translated");
        node.parentElement.removeAttribute("data-linguapay-tier");
        node.parentElement.removeAttribute("title");
      }
    }
    for (const el of this.trackedPlaceholders) {
      const origPh = this.originalPlaceholderMap.get(el);
      if (origPh !== undefined && el.isConnected) {
        el.placeholder = origPh;
      }
      el.removeAttribute("data-linguapay-ph-translated");
    }
  }

  clearTracking(): void {
    this.trackedTextNodes.clear();
    this.trackedPlaceholders.clear();
  }
}
