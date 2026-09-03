const TriageController = {
  openModal() {
    document.getElementById('triage-modal-overlay').classList.add('active');
    document.getElementById('triage-modal').classList.add('active');
    this.nextStep(1);
  },

  closeModal() {
    document.getElementById('triage-modal-overlay').classList.remove('active');
    document.getElementById('triage-modal').classList.remove('active');
  },

  nextStep(stepNum) {
    document.querySelectorAll('.tm-step').forEach(el => el.classList.remove('active'));
    document.getElementById(`tm-step-${stepNum}`).classList.add('active');
  },

  analyzeVitals() {
    const bpInput = document.getElementById('tm-bp').value.trim();
    const symptom = document.getElementById('tm-symptoms').value;
    
    let isRedFlag = false;
    let reason = "";

    // Super simple heuristic for the demo
    if (symptom === 'chest_pain' || symptom === 'trauma' || symptom === 'pregnancy_danger' || symptom === 'breathless') {
      isRedFlag = true;
      reason = `Critical symptom selected: ${symptom.replace('_', ' ').toUpperCase()}`;
    }

    if (bpInput) {
      const parts = bpInput.split('/');
      if (parts.length === 2) {
        const sys = parseInt(parts[0]);
        if (sys >= 140) {
          isRedFlag = true;
          reason = `High Blood Pressure detected (${bpInput}). High Risk Pregnancy Danger Sign.`;
        }
      }
    }

    if (isRedFlag) {
      document.getElementById('tm-risk-reason').innerText = reason;
      this.nextStep(3); // Go to red flag step
    } else {
      // Just close it if it's fine
      alert("Routine Registration Complete. No red flags detected.");
      this.closeModal();
    }
  },

  triggerEmergencyReferral() {
    this.closeModal();
    const symptom = document.getElementById('tm-symptoms').value;
    
    let erType = 'cardiac';
    if (symptom === 'trauma') erType = 'trauma';
    if (symptom === 'pregnancy_danger') erType = 'pediatric'; // best fit for now
    if (symptom === 'breathless') erType = 'breathing';
    
    if (window.EmergencyController) {
      window.EmergencyController.setTriage(erType);
    }
  }
};

// Expose to window for inline onclick handlers
window.TriageController = TriageController;
