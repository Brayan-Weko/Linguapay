(function () {
  "use strict";

  const I18N = {
    fr: {
      subtitle: "Portail Bancaire Numérique de Démonstration (Environnement Simulé)",
      simBadge: "OPÉRATIONS SIMULÉES",
      altSkin: "Interface Microfinance →",
      secTitle: "Attention : ne communiquez jamais votre code PIN.",
      secBody: "Un agent officiel ne vous demandera jamais votre mot de passe ni votre code secret par téléphone ou par message.",
      dashTitle: "Consultation de compte",
      statusActive: "Compte actif",
      availBalance: "Solde disponible",
      recentTitle: "Dernières opérations simulées",
      tx1Label: "Paiement marchand — Marché Mokolo",
      tx2Label: "Dépôt agence — Yaoundé Centre",
      alertsTitle: "Messages et alertes du service",
      clearBtn: "Effacer",
      welcomeInfo: "Les virements nationaux sont traités instantanément. Vérifiez toujours le montant et le bénéficiaire avant confirmation.",
      transferTitle: "Préparer un transfert vers un bénéficiaire",
      feeRateTag: "Barème : 1,5 % + 750 FCFA",
      lblRecipientName: "Nom du bénéficiaire",
      lblRecipientPhone: "Numéro du bénéficiaire (+237)",
      lblAmount: "Montant à envoyer (FCFA)",
      lblReason: "Motif de l'opération",
      feePrincipal: "Montant principal",
      totalDebit: "Total à débiter",
      btnContinue: "Continuer",
      btnErrBalance: "Simuler solde insuffisant",
      btnErrLimit: "Simuler plafond dépassé",
      juryTitle: "Console — Injection de Contenu Inédit en Direct",
      juryDesc: "Permet d'introduire un message totalement nouveau dans le DOM pendant la démonstration afin de tester l'adaptation dynamique et la préservation des données.",
      btnInject: "Injecter ce message",
      presetMaint: "Préréglage : Maintenance",
      presetFraud: "Préréglage : Alerte fraude",
      modalTitle: "Récapitulatif avant confirmation",
      modalIrreversible: "Vérifiez attentivement le bénéficiaire et les frais. Une opération confirmée ne peut pas être annulée automatiquement.",
      lblPin: "Code secret PIN simulé (4 chiffres)",
      btnCancel: "Annuler",
      btnConfirm: "Confirmer le transfert",
      acctPrefix: "Compte courant **** 4821",
      errInsufficient: "Solde insuffisant pour effectuer cette opération.",
      errLimit: "Plafond journalier dépassé.",
      errPin: "Veuillez saisir un code PIN simulé à 4 chiffres.",
      presetMaintText: "Maintenance prévue ce dimanche de 02h00 à 04h00 : les virements internationaux seront suspendus.",
      presetFraudText: "Alerte sécurité : méfiez-vous des appels demandant de valider un transfert de 25 000 FCFA pour débloquer votre compte."
    },
    en: {
      subtitle: "Digital Banking Demo Portal (Simulated Environment)",
      simBadge: "SIMULATED OPERATIONS",
      altSkin: "Microfinance UI →",
      secTitle: "Warning: never share your PIN code.",
      secBody: "An official agent will never ask for your password or secret PIN by phone or message.",
      dashTitle: "Account overview",
      statusActive: "Active account",
      availBalance: "Available balance",
      recentTitle: "Recent simulated transactions",
      tx1Label: "Merchant payment — Mokolo Market",
      tx2Label: "Branch deposit — Yaoundé Center",
      alertsTitle: "Service messages and alerts",
      clearBtn: "Clear",
      welcomeInfo: "Domestic transfers are processed instantly. Always verify the amount and recipient before confirming.",
      transferTitle: "Prepare a transfer to a beneficiary",
      feeRateTag: "Fee schedule: 1.5% + 750 FCFA",
      lblRecipientName: "Recipient name",
      lblRecipientPhone: "Recipient phone (+237)",
      lblAmount: "Amount to send (FCFA)",
      lblReason: "Operation reason",
      feePrincipal: "Principal amount",
      totalDebit: "Total to be debited",
      btnContinue: "Continue",
      btnErrBalance: "Simulate insufficient balance",
      btnErrLimit: "Simulate daily limit exceeded",
      juryTitle: "Console — Live Unseen Content Injection",
      juryDesc: "Allows introducing a completely new message into the DOM during the demo to evaluate dynamic adaptation and data preservation.",
      btnInject: "Inject message",
      presetMaint: "Preset: Maintenance",
      presetFraud: "Preset: Fraud alert",
      modalTitle: "Summary before confirmation",
      modalIrreversible: "Carefully check the beneficiary and fees. A confirmed transaction cannot be reversed automatically.",
      lblPin: "Simulated secret PIN (4 digits)",
      btnCancel: "Cancel",
      btnConfirm: "Confirm transfer",
      acctPrefix: "Checking account **** 4821",
      errInsufficient: "Insufficient balance to complete this transaction.",
      errLimit: "Daily limit exceeded.",
      errPin: "Please enter a 4-digit simulated PIN code.",
      presetMaintText: "Scheduled maintenance this Sunday from 02:00 to 04:00: international transfers will be paused.",
      presetFraudText: "Security alert: beware of calls asking you to approve a 25,000 FCFA transfer to unlock your account."
    }
  };

  let currentLang = "fr";
  let currentBalance = 145750;
  let txCounter = 9942;

  function formatFcfa(value) {
    return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " FCFA";
  }

  function computeFee(amount) {
    if (!Number.isFinite(amount) || amount <= 0) return 0;
    return Math.round(amount * 0.015 + 750);
  }

  function updateBalanceDisplay() {
    document.getElementById("account-balance").textContent = formatFcfa(currentBalance);
  }

  function updateFeePreview() {
    const amount = Number(document.getElementById("transfer-amount").value) || 0;
    const fee = computeFee(amount);
    const total = amount + fee;
    const pct = amount > 0 ? ((fee / amount) * 100).toFixed(2).replace(".", currentLang === "fr" ? "," : ".") : "0";

    document.getElementById("preview-principal").textContent = formatFcfa(amount);
    document.getElementById("preview-fee").textContent = formatFcfa(fee);
    document.getElementById("preview-total").textContent = formatFcfa(total);

    const feeLabelEl = document.querySelector('[data-i18n="feeLabel"]');
    feeLabelEl.textContent =
      currentLang === "fr"
        ? `Frais de transaction (${pct} %)`
        : `Transaction fee (${pct}%)`;
  }

  function setLang(lang) {
    currentLang = lang;
    document.documentElement.lang = lang;
    document.getElementById("btn-lang-fr").classList.toggle("active", lang === "fr");
    document.getElementById("btn-lang-en").classList.toggle("active", lang === "en");

    const dict = I18N[lang];
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });
    document.getElementById("account-number").textContent = dict.acctPrefix;
    updateFeePreview();
  }

  function showFormError(message) {
    const container = document.getElementById("form-error-container");
    container.innerHTML = "";
    const box = document.createElement("div");
    box.className = "alert-box alert-error";
    box.setAttribute("role", "alert");
    box.textContent = message;
    container.appendChild(box);
  }

  function clearFormError() {
    document.getElementById("form-error-container").innerHTML = "";
  }

  function appendDynamicMessage(text) {
    if (!text.trim()) return;
    const feed = document.getElementById("dynamic-feed");
    const item = document.createElement("div");
    item.className = "dynamic-msg";
    item.textContent = text.trim();
    feed.prepend(item);
  }

  function openSummaryModal() {
    clearFormError();
    const name = document.getElementById("recipient-name").value.trim();
    const phone = document.getElementById("recipient-phone").value.trim();
    const amount = Number(document.getElementById("transfer-amount").value) || 0;
    const fee = computeFee(amount);
    const total = amount + fee;

    if (total > currentBalance) {
      showFormError(I18N[currentLang].errInsufficient);
      return;
    }

    const summaryEl = document.getElementById("modal-summary-sentence");
    summaryEl.textContent =
      currentLang === "fr"
        ? `Vous allez transférer ${formatFcfa(amount)} à ${name} (${phone}). Frais : ${formatFcfa(fee)}. Total à débiter : ${formatFcfa(total)}.`
        : `You are about to transfer ${formatFcfa(amount)} to ${name} (${phone}). Fee: ${formatFcfa(fee)}. Total to be debited: ${formatFcfa(total)}.`;

    document.getElementById("mock-pin").value = "";
    document.getElementById("modal-pin-error").innerHTML = "";
    document.getElementById("summary-modal").classList.remove("hidden");
  }

  function confirmTransfer() {
    const pin = document.getElementById("mock-pin").value.trim();
    if (!/^\d{4}$/.test(pin)) {
      const errDiv = document.getElementById("modal-pin-error");
      errDiv.innerHTML = `<div class="alert-box alert-error">${I18N[currentLang].errPin}</div>`;
      return;
    }

    const name = document.getElementById("recipient-name").value.trim();
    const amount = Number(document.getElementById("transfer-amount").value) || 0;
    const fee = computeFee(amount);
    const total = amount + fee;
    currentBalance = Math.max(0, currentBalance - total);
    txCounter += 1;

    updateBalanceDisplay();
    document.getElementById("summary-modal").classList.add("hidden");

    const ref = `TX-2026-${txCounter}`;
    const txList = document.getElementById("tx-history");
    const li = document.createElement("li");
    li.className = "tx-item";
    li.innerHTML = `
      <div>
        <strong>${currentLang === "fr" ? "Transfert vers" : "Transfer to"} ${name}</strong>
        <div class="tx-ref">${ref} &bull; ${currentLang === "fr" ? "À l'instant" : "Just now"}</div>
      </div>
      <span style="color:#dc2626; font-weight:700;">-${formatFcfa(total)}</span>
    `;
    txList.prepend(li);

    const alertsArea = document.getElementById("service-alerts-area");
    const ok = document.createElement("div");
    ok.className = "alert-box alert-success";
    ok.textContent =
      currentLang === "fr"
        ? `Transfert simulé confirmé (${ref}) : ${formatFcfa(amount)} envoyés à ${name}.`
        : `Simulated transfer confirmed (${ref}): ${formatFcfa(amount)} sent to ${name}.`;
    alertsArea.prepend(ok);
  }

  // Event wiring
  document.getElementById("btn-lang-fr").addEventListener("click", () => setLang("fr"));
  document.getElementById("btn-lang-en").addEventListener("click", () => setLang("en"));
  document.getElementById("transfer-amount").addEventListener("input", updateFeePreview);

  document.getElementById("transfer-form").addEventListener("submit", (e) => {
    e.preventDefault();
    openSummaryModal();
  });

  document.getElementById("btn-sim-insufficient").addEventListener("click", () => {
    showFormError(I18N[currentLang].errInsufficient);
  });

  document.getElementById("btn-sim-limit").addEventListener("click", () => {
    showFormError(I18N[currentLang].errLimit);
  });

  document.getElementById("btn-modal-cancel").addEventListener("click", () => {
    document.getElementById("summary-modal").classList.add("hidden");
  });

  document.getElementById("btn-modal-confirm").addEventListener("click", confirmTransfer);

  document.getElementById("btn-clear-alerts").addEventListener("click", () => {
    document.getElementById("dynamic-feed").innerHTML = "";
  });

  document.getElementById("btn-inject-custom").addEventListener("click", () => {
    const input = document.getElementById("jury-custom-input");
    appendDynamicMessage(input.value);
    input.value = "";
  });

  document.getElementById("btn-preset-maint").addEventListener("click", () => {
    appendDynamicMessage(I18N[currentLang].presetMaintText);
  });

  document.getElementById("btn-preset-fraud").addEventListener("click", () => {
    appendDynamicMessage(I18N[currentLang].presetFraudText);
  });

  updateBalanceDisplay();
  updateFeePreview();
})();

