const form = document.getElementById("calc-form");
const resultsEl = document.getElementById("results");
const gcsLT15El = document.getElementById("gcs_lt15");
const dnRatioEl = document.getElementById("dn_ratio");
const neckGT4El = document.getElementById("neck_gt4");
const resetBtn = document.getElementById("reset");

function valOrNull(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  const v = el.value.trim();
  if (v === "") return null;
  if (["age", "gcs", "dome", "neck"].includes(id)) return Number(v);
  if (["htn","cvd","smoke","famHist","wfns","hemiparesis","ruptured","dm","daughter","ptosis","seizure","multiple","iom"].includes(id)) {
    return v === "" ? null : Number(v);
  }
  if (id === "location") return v === "" ? null : v;
  return v;
}

async function predict() {
  const payload = {
    age: valOrNull("age"),
    gcs: valOrNull("gcs"),
    wfns: valOrNull("wfns"),
    htn: valOrNull("htn"),
    dm: valOrNull("dm"),
    cvd: valOrNull("cvd"),
    smoke: valOrNull("smoke"),
    famHist: valOrNull("famHist"),
    ruptured: valOrNull("ruptured"),
    hemiparesis: valOrNull("hemiparesis"),
    ptosis: valOrNull("ptosis"),
    seizure: valOrNull("seizure"),
    multiple: valOrNull("multiple"),
    iom: valOrNull("iom"),
    location: valOrNull("location"),
    dome: valOrNull("dome"),
    neck: valOrNull("neck"),
  };

  const res = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    alert("Server error. Check console/logs.");
    return;
  }
  const data = await res.json();
  renderDerived(data.derived);
  renderResults(data);
}

function renderDerived(d) {
  gcsLT15El.textContent = d.gcs_lt15 === null ? "—" : (d.gcs_lt15 ? "Yes" : "No");
  dnRatioEl.textContent = d.dn_ratio === null ? "—" : d.dn_ratio;
  neckGT4El.textContent = d.neck_gt4 === null ? "—" : (d.neck_gt4 ? "Yes" : "No");
}

function chip(label) { return `<span class="badge">${label}</span>`; }

function resultCard(title, percent, logit, auc, missingList) {
  const ok = !missingList || missingList.length === 0;
  const missHtml = ok ? `<span class="ok">All predictors present</span>` : `<span class="miss">Missing: ${missingList.join(", ")}</span>`;
  return `
    <div class="card result">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <h3>${title}</h3>
        <div class="badges">${chip(`AUC ${auc}`)}</div>
      </div>
      <div class="percent">${percent}%</div>
      <div>logit: ${logit}</div>
      <div>${missHtml}</div>
    </div>
  `;
}

function renderResults(p) {
  const cards = [
    resultCard("Mortality if COIL", p.mortality_coil, "-", 0.826, []),
    resultCard("Mortality if CLIP", p.mortality_clip, "-", 0.815, []),
    resultCard("Good GOSE (5–8) if COIL", p.good_gose_coil, "-", 0.707, []),
    resultCard("Good GOSE (5–8) if CLIP", p.good_gose_clip, "-", 0.793, []),
    resultCard("GCS baseline if COIL", p.gcs_recovery_coil, "-", 0.768, []),
    resultCard("GCS baseline if CLIP", p.gcs_recovery_clip, "-", 0.765, []),
  ];
  // If you want to show logits & missing variables, switch backend to return those fields too.
  resultsEl.innerHTML = cards.join("");
}

form.addEventListener("submit", (e) => { e.preventDefault(); predict(); });
resetBtn.addEventListener("click", () => { form.reset(); resultsEl.innerHTML = ""; renderDerived({gcs_lt15:null,dn_ratio:null,neck_gt4:null}); });
renderDerived({ gcs_lt15: null, dn_ratio: null, neck_gt4: null });
