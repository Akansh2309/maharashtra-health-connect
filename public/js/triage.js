const TriageController = {
  openModal() {
    document.getElementById('triage-modal-overlay').classList.add('active');
    document.getElementById('triage-modal').classList.add('active');
    this.nextStep(1);
    this.setupAutocomplete();
  },

  closeModal() {
    document.getElementById('triage-modal-overlay').classList.remove('active');
    document.getElementById('triage-modal').classList.remove('active');
  },

  nextStep(stepNum) {
    document.querySelectorAll('.tm-step').forEach(el => el.classList.remove('active'));
    document.getElementById(`tm-step-${stepNum}`).classList.add('active');
  },

  setupAutocomplete() {
    const searchInput = document.getElementById('tm-symptoms-search');
    const resultsBox = document.getElementById('tm-symptoms-autocomplete');
    const hiddenId = document.getElementById('tm-symptoms');
    let debounceTimer;

    if (!searchInput) return;

    // Reset it
    searchInput.value = '';
    hiddenId.value = '';

    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value;
        
        if (query.length < 2) {
            resultsBox.style.display = 'none';
            return;
        }
        
        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch('/api/symptoms/search?q=' + encodeURIComponent(query));
                const symptoms = await res.json();
                
                if (symptoms.length > 0) {
                    resultsBox.innerHTML = symptoms.map(s => `
                        <div class="symptom-item" data-id="${s.id}" data-name="${s.name}" style="padding: 10px; border-bottom: 1px solid #eee; cursor: pointer;">
                            <strong style="color: #0056b3;">${s.name}</strong> <small style="color: #666;">(${s.id})</small>
                        </div>
                    `).join('');
                    resultsBox.style.display = 'block';
                    
                    document.querySelectorAll('.symptom-item').forEach(item => {
                        item.addEventListener('click', () => {
                            searchInput.value = item.getAttribute('data-name');
                            hiddenId.value = item.getAttribute('data-id');
                            resultsBox.style.display = 'none';
                        });
                        item.addEventListener('mouseover', () => {
                            item.style.backgroundColor = '#f0f8ff';
                        });
                        item.addEventListener('mouseout', () => {
                            item.style.backgroundColor = 'transparent';
                        });
                    });
                } else {
                    resultsBox.innerHTML = '<div style="padding: 10px; color: #888;">No matches found in HPO Database</div>';
                    resultsBox.style.display = 'block';
                }
            } catch(err) {
                console.error("Failed to search symptoms", err);
            }
        }, 300);
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !resultsBox.contains(e.target)) {
            resultsBox.style.display = 'none';
        }
    });
  },

  async analyzeVitals() {
    const bpInput = document.getElementById('tm-bp').value.trim();
    const symptomId = document.getElementById('tm-symptoms').value;
    const symptomName = document.getElementById('tm-symptoms-search').value;
    
    if (!symptomId) {
        alert("Please search and select a valid symptom from the HPO Database.");
        return;
    }

    this.nextStep(3); // Go to red flag step
    const reasonEl = document.getElementById('tm-risk-reason');
    reasonEl.innerHTML = `<span style="color: #0056b3;">Analyzing HPO Matrix (8900+ paths)...</span>`;
    
    // Hide default routing button until we know the specialty
    const actionBtn = document.querySelector('#tm-step-3 .btn-danger');
    if (actionBtn) actionBtn.style.display = 'none';

    try {
        const response = await fetch('/api/triage/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms: [symptomId] })
        });
        const data = await response.json();
        
        if (data.diseases && data.diseases.length > 0) {
            const topDisease = data.diseases[0];
            this.lastRecommendedSpecialty = data.recommended_specialty;
            
            reasonEl.innerHTML = `
                <div style="background: #fff3f3; padding: 12px; border-radius: 6px; border-left: 4px solid #d32f2f; margin-bottom: 10px; text-align: left;">
                    <div style="color: #d32f2f; font-weight: bold; margin-bottom: 5px;">⚠️ HIGH RISK HPO MATCH</div>
                    <strong>Disease:</strong> ${topDisease.name}<br>
                    <strong>Routing to:</strong> ${data.raw_specialty}<br>
                    <small style="color: #666;">Match Confidence: High</small>
                </div>
            `;
            
            if (bpInput) {
                const parts = bpInput.split('/');
                if (parts.length === 2 && parseInt(parts[0]) >= 140) {
                    reasonEl.innerHTML += `<div style="color: #d32f2f; font-weight: bold; text-align:left;">+ High Blood Pressure detected (${bpInput})</div>`;
                }
            }

            if (actionBtn) {
                actionBtn.innerText = `Find ${data.raw_specialty} Facility`;
                actionBtn.style.display = 'block';
                // override onclick
                actionBtn.onclick = () => this.triggerEmergencyReferral();
            }

        } else {
            reasonEl.innerHTML = `
                <div style="color: #137333; font-weight: bold; margin-bottom: 10px;">✅ Routine Care</div>
                No critical disease match found for ${symptomName}.
            `;
            if (actionBtn) {
                actionBtn.innerText = `Complete Routine Registration`;
                actionBtn.classList.remove('btn-danger');
                actionBtn.classList.add('btn-primary');
                actionBtn.style.display = 'block';
                actionBtn.onclick = () => {
                    alert("Routine Registration Complete.");
                    this.closeModal();
                };
            }
        }
    } catch (err) {
        reasonEl.innerHTML = `<span style="color: red;">Analysis Error: ${err.message}</span>`;
    }
  },

  triggerEmergencyReferral() {
    this.closeModal();
    if (window.EmergencyController && this.lastRecommendedSpecialty) {
      window.EmergencyController.setTriage(this.lastRecommendedSpecialty);
    } else if (window.EmergencyController) {
      window.EmergencyController.setTriage('general');
    }
  }
};

window.TriageController = TriageController;
