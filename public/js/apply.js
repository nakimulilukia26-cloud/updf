// ============================================================
// UPDF Recruitment Portal - Application Form JavaScript
// ============================================================

let currentStep = 1;
const totalSteps = 6;

document.addEventListener("DOMContentLoaded", function () {
  loadDistricts();
  setupDOBListener();
  setupNINChecker();
  setupFileUploads();
  updateNav();
});

function loadDistricts() {
  fetch("/api/districts")
    .then((r) => r.json())
    .then((data) => {
      const districts = data.data;
      ["district_of_origin", "district_of_residence"].forEach((id) => {
        const sel = document.getElementById(id);
        if (!sel) return;
        districts.forEach((d) => {
          const opt = document.createElement("option");
          opt.value = d;
          opt.textContent = d;
          sel.appendChild(opt);
        });
      });
    });
}

function setupDOBListener() {
  const dobInput = document.getElementById("date_of_birth");
  if (!dobInput) return;

  const today = new Date();
  const maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
  dobInput.max = maxDate.toISOString().split("T")[0];

  dobInput.addEventListener("change", function () {
    const dob = new Date(this.value);
    const age = Math.floor((today - dob) / (365.25 * 24 * 60 * 60 * 1000));
    const display = document.getElementById("ageDisplay");
    if (display) {
      if (age < 18) {
        display.textContent = `Age: ${age} years (Must be at least 18 years old)`;
        display.style.color = "var(--danger)";
      } else {
        display.textContent = `Age: ${age} years`;
        display.style.color = "var(--success)";
      }
    }
  });
}

let ninTimer = null;
function setupNINChecker() {
  const ninInput = document.getElementById("national_id");
  if (!ninInput) return;
  ninInput.addEventListener("input", function () {
    clearTimeout(ninTimer);
    const val = this.value.trim().toUpperCase();
    if (val.length < 14) return;
    ninTimer = setTimeout(() => {
      fetch(`/api/check-nin/${encodeURIComponent(val)}`)
        .then((r) => r.json())
        .then((data) => {
          const statusEl = document.getElementById("ninStatus");
          if (data.exists) {
            statusEl.textContent = "This National ID already has a submitted application.";
            statusEl.style.color = "var(--danger)";
            ninInput.classList.add("error");
          } else if (val.length >= 14) {
            statusEl.textContent = "National ID available.";
            statusEl.style.color = "var(--success)";
            ninInput.classList.remove("error");
          }
        });
    }, 600);
  });
}

function setupFileUploads() {
  document.querySelectorAll(".file-upload-box").forEach((box) => {
    box.addEventListener("dragover", (e) => {
      e.preventDefault();
      box.classList.add("dragover");
    });
    box.addEventListener("dragleave", () => box.classList.remove("dragover"));
    box.addEventListener("drop", (e) => {
      e.preventDefault();
      box.classList.remove("dragover");
      const input = box.querySelector("input[type=file]");
      if (input && e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        const previewId = input.getAttribute("onchange").match(/'([^']+)'/)?.[1];
        if (previewId) showFile(input, previewId);
      }
    });
  });
}

function showFile(input, previewId) {
  const file = input.files[0];
  if (!file) return;
  const preview = document.getElementById(previewId);
  if (!preview) return;
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
  if (file.size > 5 * 1024 * 1024) {
    showToast("File too large. Maximum size is 5MB.", "error");
    input.value = "";
    preview.style.display = "none";
    return;
  }
  preview.style.display = "block";
  preview.textContent = `OK ${file.name} (${sizeMB}MB)`;
}

function toggleSection(id, show) {
  const el = document.getElementById(id);
  if (el) el.style.display = show ? "block" : "none";
}

function nextStep() {
  if (!validateStep(currentStep)) return;
  if (currentStep === totalSteps) {
    submitApplication();
    return;
  }
  goToStep(currentStep + 1);
}

function prevStep() {
  if (currentStep > 1) goToStep(currentStep - 1);
}

function goToStep(step) {
  document.getElementById(`step${currentStep}`).classList.remove("active");
  document.querySelectorAll(".progress-step")[currentStep - 1].classList.remove("active");
  document.querySelectorAll(".progress-step")[currentStep - 1].classList.add("completed");

  currentStep = step;
  document.getElementById(`step${currentStep}`).classList.add("active");

  const steps = document.querySelectorAll(".progress-step");
  steps.forEach((s, i) => {
    if (i < currentStep - 1) { s.classList.add("completed"); s.classList.remove("active"); }
    else if (i === currentStep - 1) { s.classList.add("active"); s.classList.remove("completed"); }
    else { s.classList.remove("active", "completed"); }
  });

  if (currentStep === totalSteps) buildSummary();
  updateNav();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateNav() {
  document.getElementById("btnPrev").disabled = currentStep === 1;
  const btnNext = document.getElementById("btnNext");
  const indicator = document.getElementById("stepIndicator");
  indicator.textContent = `Step ${currentStep} of ${totalSteps}`;

  if (currentStep === totalSteps) {
    btnNext.textContent = "Submit Application";
    btnNext.style.background = "var(--success)";
    btnNext.style.borderColor = "var(--success)";
  } else {
    btnNext.textContent = "Next Step";
    btnNext.style.background = "";
    btnNext.style.borderColor = "";
  }
}

function showError(id, show) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.toggle("show", show);
    const input = el.previousElementSibling;
    if (input && input.classList) {
      input.classList.toggle("error", show);
    }
  }
}

function val(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : "";
}

function validateStep(step) {
  let valid = true;

  if (step === 1) {
    if (!val("surname")) { showError("err_surname", true); valid = false; } else showError("err_surname", false);
    if (!val("given_names")) { showError("err_given_names", true); valid = false; } else showError("err_given_names", false);
    if (!val("date_of_birth")) { showError("err_dob", true); valid = false; } else {
      const dob = new Date(val("date_of_birth"));
      const age = Math.floor((new Date() - dob) / (365.25 * 24 * 60 * 60 * 1000));
      if (age < 18) { showToast("You must be at least 18 years old to apply.", "error"); valid = false; }
      showError("err_dob", false);
    }
    if (!val("gender")) { showError("err_gender", true); valid = false; } else showError("err_gender", false);
    if (!val("national_id") || val("national_id").length < 10) { showError("err_nin", true); valid = false; } else showError("err_nin", false);
  }

  if (step === 2) {
    const phone = val("phone");
    if (!phone || !/^0[0-9]{9}$/.test(phone.replace(/\s/g, ""))) {
      showError("err_phone", true); valid = false;
    } else showError("err_phone", false);
    if (!val("district_of_origin")) { showError("err_district_origin", true); valid = false; } else showError("err_district_origin", false);
    if (!val("sub_county") || !val("parish") || !val("village")) {
      showToast("Please fill in all location fields.", "error"); valid = false;
    }
    if (!val("nok_name") || !val("nok_relationship") || !val("nok_phone") || !val("nok_address")) {
      showToast("Please fill in all Next of Kin fields.", "error"); valid = false;
    }
  }

  if (step === 5) {
    if (!document.getElementById("passport_photo").files.length) {
      showError("err_passport", true); valid = false;
    } else showError("err_passport", false);
    if (!document.getElementById("national_id_doc").files.length) {
      showError("err_nid_doc", true); valid = false;
    } else showError("err_nid_doc", false);
  }

  if (step === 6) {
    if (!document.getElementById("declaration_accepted").checked) {
      showError("err_declaration", true); valid = false;
    } else showError("err_declaration", false);
  }

  if (!valid) showToast("Please correct the highlighted errors.", "error");
  return valid;
}

function buildSummary() {
  const category = document.querySelector('input[name="recruitment_category"]:checked')?.value;
  const proCategory = val("professional_category");
  const gender = val("gender");
  const district = val("district_of_origin");

  const summaryEl = document.getElementById("summaryContent");
  if (!summaryEl) return;

  summaryEl.innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div><strong>Name:</strong> ${val("surname")}, ${val("given_names")}</div>
      <div><strong>National ID:</strong> ${val("national_id")}</div>
      <div><strong>Date of Birth:</strong> ${val("date_of_birth")}</div>
      <div><strong>Gender:</strong> ${gender}</div>
      <div><strong>District of Origin:</strong> ${district}</div>
      <div><strong>District of Residence:</strong> ${val("district_of_residence")}</div>
      <div><strong>Phone:</strong> ${val("phone")}</div>
      <div><strong>Email:</strong> ${val("email") || "Not provided"}</div>
      <div><strong>Category:</strong> ${category}${proCategory ? " - " + proCategory : ""}</div>
    </div>
    <div style="margin-top:10px;padding:10px;background:white;border-radius:6px;border:1px solid var(--border)">
      <strong>Documents:</strong>
      ${document.getElementById("passport_photo").files.length ? "OK Passport Photo  " : "Passport Photo MISSING  "}
      ${document.getElementById("national_id_doc").files.length ? "OK National ID  " : "National ID MISSING  "}
      ${document.getElementById("uce_certificate").files.length ? "OK UCE Certificate  " : ""}
      ${document.getElementById("uace_certificate").files.length ? "OK UACE Certificate  " : ""}
      ${document.getElementById("degree_certificate").files.length ? "OK Degree/Diploma  " : ""}
    </div>
  `;
}

function submitApplication() {
  if (!validateStep(6)) return;

  const btnNext = document.getElementById("btnNext");
  btnNext.disabled = true;
  btnNext.innerHTML = 'Submitting...';

  const formData = new FormData(document.getElementById("applyForm"));

  const category = document.querySelector('input[name="recruitment_category"]:checked')?.value;
  if (category) formData.set("recruitment_category", category);

  fetch("/apply/submit", {
    method: "POST",
    body: formData,
  })
    .then((r) => r.json())
    .then((data) => {
      btnNext.disabled = false;
      btnNext.innerHTML = "Submit Application";

      if (data.success) {
        document.getElementById("resultAppNumber").textContent = data.application_number;
        document.getElementById("resultName").textContent = `Applicant: ${data.applicant_name}`;
        document.getElementById("successModal").classList.add("show");
      } else {
        showToast(data.message || "Submission failed. Please try again.", "error");
      }
    })
    .catch((err) => {
      btnNext.disabled = false;
      btnNext.innerHTML = "Submit Application";
      showToast("Network error. Please check your connection and try again.", "error");
    });
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}