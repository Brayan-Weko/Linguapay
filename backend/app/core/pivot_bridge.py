"""Universal Language Pivot Bridge: translates any source language to English pivot,
then into Cameroonian national languages while strictly preserving EntityShield tokens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Common multilingual financial keywords mapped directly to English canonical forms
MULTILINGUAL_FINANCIAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Spanish (es)
    (re.compile(r"\bSaldo disponible\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\bComisi[oó]n de transferencia\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bComisi[oó]n de transacci[oó]n\b", re.IGNORECASE), "Transaction fee"),
    (re.compile(r"\bTotal a debitar\b", re.IGNORECASE), "Total to be debited"),
    (re.compile(r"\bEnviar dinero\b", re.IGNORECASE), "Send money"),
    (re.compile(r"\bPreparar una transferencia\b", re.IGNORECASE), "Prepare a transfer"),
    (re.compile(r"\bBeneficiario\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bCantidad a enviar\b", re.IGNORECASE), "Amount to send"),
    (re.compile(r"\bResumen antes de la confirmaci[oó]n\b", re.IGNORECASE), "Summary before confirmation"),
    (re.compile(r"\bConfirmar la transferencia\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bSaldo insuficiente para realizar esta operaci[oó]n\b", re.IGNORECASE), "Insufficient balance to complete this transaction."),
    (re.compile(r"\bSaldo insuficiente\b", re.IGNORECASE), "Insufficient balance"),
    (re.compile(r"\bL[ií]mite diario superado\b", re.IGNORECASE), "Daily limit exceeded."),
    (re.compile(r"\bAtenci[oó]n\s*:\s*nunca comparta su c[oó]digo PIN\b", re.IGNORECASE), "Warning: never share your PIN code."),
    (re.compile(r"\bUn agente oficial nunca le pedir[aá] su contrase[nñ]a\b", re.IGNORECASE), "An official agent will never ask for your password."),

    # German (de)
    (re.compile(r"\bVerf[uü]gbares Guthaben\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\b[UÜ]berweisungsgeb[uü]hr\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bTransaktionsgeb[uü]hr\b", re.IGNORECASE), "Transaction fee"),
    (re.compile(r"\bZu belastender Gesamtbetrag\b", re.IGNORECASE), "Total to be debited"),
    (re.compile(r"\bGeld senden\b", re.IGNORECASE), "Send money"),
    (re.compile(r"\bEmpf[aä]nger\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bZu sendender Betrag\b", re.IGNORECASE), "Amount to send"),
    (re.compile(r"\b[UÜ]berweisung best[aä]tigen\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bUnzureichender Kontostand\b", re.IGNORECASE), "Insufficient balance"),
    (re.compile(r"\bTageslimit [uü]berschritten\b", re.IGNORECASE), "Daily limit exceeded."),
    (re.compile(r"\bAchtung\s*:\s*Geben Sie niemals Ihren PIN-Code weiter\b", re.IGNORECASE), "Warning: never share your PIN code."),

    # Portuguese (pt)
    (re.compile(r"\bSaldo dispon[ií]vel\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\bTaxa de transfer[eê]ncia\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bTotal a debitar\b", re.IGNORECASE), "Total to be debited"),
    (re.compile(r"\bBenefici[aá]rio\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bConfirmar transfer[eê]ncia\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bSaldo insuficiente\b", re.IGNORECASE), "Insufficient balance"),
    (re.compile(r"\bAten[cç][aã]o\s*:\s*nunca compartilhe seu c[oó]digo PIN\b", re.IGNORECASE), "Warning: never share your PIN code."),

    # Italian (it)
    (re.compile(r"\bSaldo disponibile\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\bCommissione di trasferimento\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bTotale da addebitare\b", re.IGNORECASE), "Total to be debited"),
    (re.compile(r"\bBeneficiario\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bConferma trasferimento\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bSaldo insufficiente\b", re.IGNORECASE), "Insufficient balance"),
    (re.compile(r"\bAttenzione\s*:\s*non condividere mai il codice PIN\b", re.IGNORECASE), "Warning: never share your PIN code."),

    # Swahili (sw)
    (re.compile(r"\bSalio lililopo\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\bGharama ya uhamisho\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bMpokeaji\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bThibitisha uhamisho\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bSalio haitoshi\b", re.IGNORECASE), "Insufficient balance"),

    # Arabic (ar)
    (re.compile(r"الرصيد المتاح"), "Available balance"),
    (re.compile(r"رسوم التحويل"), "Transfer fee"),
    (re.compile(r"المستفيد"), "Beneficiary"),
    (re.compile(r"تأكيد التحويل"), "Confirm transfer"),
    (re.compile(r"رصيد غير كاف"), "Insufficient balance"),
    (re.compile(r"تحذير\s*:\s*لا تشارك رمز PIN الخاص بك أبداً"), "Warning: never share your PIN code."),

    # Chinese Simplified (zh)
    (re.compile(r"可用余额"), "Available balance"),
    (re.compile(r"转账费用"), "Transfer fee"),
    (re.compile(r"收款人"), "Beneficiary"),
    (re.compile(r"确认转账"), "Confirm transfer"),
    (re.compile(r"余额不足"), "Insufficient balance"),
    (re.compile(r"警告[：:]\s*切勿透露您的PIN码"), "Warning: never share your PIN code."),

    # Russian (ru)
    (re.compile(r"\bДоступный баланс\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\bКомиссия за перевод\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bПолучатель\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bПодтвердить перевод\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bНедостаточно средств\b", re.IGNORECASE), "Insufficient balance"),
    (re.compile(r"\bВнимание\s*:\s*никогда не сообщайте свой PIN-код\b", re.IGNORECASE), "Warning: never share your PIN code."),

    # Turkish (tr)
    (re.compile(r"\bKullan[iı]labilir bakiye\b", re.IGNORECASE), "Available balance"),
    (re.compile(r"\bTransfer [uü]creti\b", re.IGNORECASE), "Transfer fee"),
    (re.compile(r"\bAl[iı]c[iı]\b", re.IGNORECASE), "Beneficiary"),
    (re.compile(r"\bTransferi onayla\b", re.IGNORECASE), "Confirm transfer"),
    (re.compile(r"\bYetersiz bakiye\b", re.IGNORECASE), "Insufficient balance"),
]


@dataclass(frozen=True)
class PivotResult:
    pivoted_text: str
    detected_source: str
    pivoted: bool


class UniversalPivotBridge:
    """Detects source language and translates to English as universal bridge
    when text is neither French nor English.
    """

    @staticmethod
    def detect_language(text: str, hint: str = "auto") -> str:
        clean_hint = (hint or "auto").lower().strip()
        if clean_hint not in ("auto", "", "unknown"):
            return clean_hint

        sample = text.lower()
        # Script heuristics
        if any("\u0600" <= c <= "\u06ff" for c in sample):
            return "ar"
        if any("\u4e00" <= c <= "\u9fff" for c in sample):
            return "zh"
        if any("\u0400" <= c <= "\u04ff" for c in sample):
            return "ru"

        # Characteristic vocabulary checks (check Portuguese before Spanish due to overlap)
        if any(w in sample for w in ["bakiye", "ücreti", "alıcı", "yetersiz"]):
            return "tr"
        if any(w in sample for w in ["disponível", "transferência", "atenção", "dinheiro", "beneficiário", "você", "não"]):
            return "pt"
        if any(w in sample for w in ["guthaben", "überweisung", "konto", "gebühr", "betrag", "achtung", "empfänger", "nicht"]):
            return "de"
        if any(w in sample for w in ["salio", "uhamisho", "mpokeaji", "thibitisha"]):
            return "sw"
        if any(w in sample for w in ["disponibile", "trasferimento", "attenzione", "denaro"]):
            return "it"
        if any(w in sample for w in ["frais", "solde", "virement", "bénéficiaire", "opération", "compte", "transférer", "attention"]):
            return "fr"
        if any(w in sample for w in ["saldo", "transferencia", "enviar", "atención", "número", "cuenta", "banco", "comisión"]):
            return "es"
        if any(w in sample for w in ["balance", "transfer", "fee", "account", "warning", "confirm", "recipient", "amount"]):
            return "en"

        return "en"

    @classmethod
    def pivot_to_english(
        cls,
        masked_text: str,
        source_lang: str = "auto",
        ai_translator: object | None = None,
    ) -> PivotResult:
        """Pivots foreign text into English canonical tokens without altering {{TOKENS}}."""
        detected = cls.detect_language(masked_text, source_lang)

        # English or French are natively supported in our packs
        if detected in ("en", "fr"):
            return PivotResult(pivoted_text=masked_text, detected_source=detected, pivoted=False)

        # Apply deterministic pattern dictionary
        pivoted = masked_text
        changed = False
        for pattern, replacement in MULTILINGUAL_FINANCIAL_PATTERNS:
            new_text, count = pattern.subn(replacement, pivoted)
            if count > 0:
                pivoted = new_text
                changed = True

        # If not matched deterministically and AI translator is available, use LLM pivot
        if not changed and ai_translator is not None and hasattr(ai_translator, "pivot_to_english"):
            llm_pivot = ai_translator.pivot_to_english(masked_text, source_lang=detected)
            if llm_pivot:
                return PivotResult(pivoted_text=llm_pivot, detected_source=detected, pivoted=True)

        return PivotResult(pivoted_text=pivoted, detected_source=detected, pivoted=changed)
