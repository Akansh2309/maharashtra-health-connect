/* 
   MH Connect — UX Enhancements JS
   All interactive UX features in one file
    */
(function() {
  'use strict';

  //  DARK MODE 
  function initDarkMode() {
    const saved = localStorage.getItem('mhc-theme');
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    document.querySelectorAll('.dark-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        localStorage.setItem('mhc-theme', isDark ? 'light' : 'dark');
        btn.textContent = isDark ? 'Dark Mode' : 'Light Mode';
      });
      btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? 'Light' : 'Dark';
    });
  }

  //  SIMPLE / ELABORATE VIEW TOGGLE 
  function initViewToggle() {
    const saved = localStorage.getItem('mhc-view') || 'simple';
    document.documentElement.setAttribute('data-view', saved);
    document.querySelectorAll('.view-toggle').forEach(btn => {
      updateViewBtn(btn, saved);
      btn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-view');
        const next = current === 'simple' ? 'elaborate' : 'simple';
        document.documentElement.setAttribute('data-view', next);
        localStorage.setItem('mhc-view', next);
        updateViewBtn(btn, next);
      });
    });
  }
  function updateViewBtn(btn, mode) {
    btn.innerHTML = mode === 'simple' ? 'Simple' : 'Detailed';
    btn.title = mode === 'simple' ? 'Switch to Detailed View' : 'Switch to Simple View';
  }

  //  SCROLL PROGRESS BAR 
  function initScrollProgress() {
    const bar = document.getElementById('scroll-progress');
    if (!bar) return;
    window.addEventListener('scroll', () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = h > 0 ? (window.scrollY / h * 100) + '%' : '0%';
    }, { passive: true });
  }

  //  SCROLL-TO-TOP BUTTON 
  function initScrollTop() {
    const btn = document.getElementById('scroll-top-btn');
    if (!btn) return;
    window.addEventListener('scroll', () => {
      btn.classList.toggle('visible', window.scrollY > 300);
    }, { passive: true });
    btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  //  COOKIE BANNER 
  function initCookieBanner() {
    const banner = document.getElementById('cookie-banner');
    if (!banner) return;
    if (localStorage.getItem('mhc-cookies-ok')) { banner.classList.add('hidden'); return; }
    banner.querySelector('.cookie-accept-btn').addEventListener('click', () => {
      localStorage.setItem('mhc-cookies-ok', '1');
      banner.classList.add('hidden');
    });
  }

  //  PAGE LOADER 
  function initPageLoader() {
    const loader = document.querySelector('.page-loader');
    if (!loader) return;
    window.addEventListener('load', () => {
      setTimeout(() => loader.classList.add('hidden'), 400);
    });
  }

  //  PASSWORD VISIBILITY TOGGLE 
  function initPwToggle() {
    document.querySelectorAll('input[type="password"]').forEach(input => {
      if (input.closest('.pw-wrapper')) return;
      const wrapper = document.createElement('div');
      wrapper.className = 'pw-wrapper';
      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pw-toggle-btn';
      btn.innerHTML = 'Show';
      btn.title = 'Show/hide password';
      btn.addEventListener('click', () => {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        btn.innerHTML = isPassword ? 'Hide' : 'Show';
      });
      wrapper.appendChild(btn);
    });
  }

  //  COPY BUTTON 
  window.mhcCopy = function(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
      const orig = btn.innerHTML;
      btn.innerHTML = 'Copied!';
      btn.classList.add('copied');
      setTimeout(() => { btn.innerHTML = orig; btn.classList.remove('copied'); }, 1500);
    });
  };

  //  MOBILE HAMBURGER MENU 
  function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger-btn');
    const overlay = document.querySelector('.mobile-nav-overlay');
    const drawer = document.querySelector('.mobile-nav-drawer');
    if (!hamburger || !overlay || !drawer) return;
    hamburger.addEventListener('click', () => {
      overlay.classList.add('open');
      drawer.classList.add('open');
    });
    overlay.addEventListener('click', closeMobileMenu);
    drawer.querySelector('.mobile-nav-close')?.addEventListener('click', closeMobileMenu);
    function closeMobileMenu() {
      overlay.classList.remove('open');
      drawer.classList.remove('open');
    }
    // populate drawer from tabs - pick only the visible language span
    document.querySelectorAll('.tab-btn[data-tab]').forEach(tab => {
      if (tab.offsetParent === null && !tab.closest('.mobile-nav-drawer')) return; // skip hidden
      const item = document.createElement('button');
      item.className = 'mobile-nav-item';
      item.setAttribute('data-tab-target', tab.getAttribute('data-tab'));
      // Get only the visible text from the correct language span
      const visibleSpan = tab.querySelector('.lang-en') || tab;
      item.textContent = visibleSpan.textContent.trim().replace(/[^\w\s-]/g, '');
      item.addEventListener('click', () => { tab.click(); closeMobileMenu(); });
      drawer.querySelector('.mobile-nav-items')?.appendChild(item);
    });
  }

  //  SITE SEARCH (within page) 
  function initSiteSearch() {
    const input = document.getElementById('site-search-input');
    if (!input) return;
    input.addEventListener('input', () => {
      const q = input.value.toLowerCase().trim();
      document.querySelectorAll('[data-searchable]').forEach(el => {
        const match = !q || el.textContent.toLowerCase().includes(q);
        el.style.display = match ? '' : 'none';
      });
    });
  }

  //  DOCTOR PRESCRIPTION SYSTEM 
  window.mhcGeneratePrescription = function() {
    const patientName = document.getElementById('rx-patient-name')?.value || 'Patient';
    const patientAge = document.getElementById('rx-patient-age')?.value || '--';
    const diseases = [];
    document.querySelectorAll('#rx-disease-list input[type="checkbox"]:checked').forEach(cb => {
      diseases.push(cb.nextElementSibling?.textContent || cb.value);
    });
    const otherDisease = document.getElementById('rx-other-disease')?.value;
    if (otherDisease) diseases.push(otherDisease);
    const medicines = document.getElementById('rx-medicines')?.value || '';
    const treatment = document.getElementById('rx-treatment')?.value || '';
    const notes = document.getElementById('rx-notes')?.value || '';

    const printArea = document.getElementById('prescription-print-area');
    if (!printArea) return;

    const today = new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
    printArea.innerHTML = `
      <h2 style="text-align:center;margin-bottom:4px;">Maharashtra Health Connect</h2>
      <p style="text-align:center;font-size:12px;color:#666;margin-bottom:16px;">Prescription — Confidential Medical Document</p>
      <hr style="border:1px solid #000;margin-bottom:16px;">
      <div class="rx-field"><span class="rx-label">Date:</span> ${today}</div>
      <div class="rx-field"><span class="rx-label">Patient Name:</span> ${patientName}</div>
      <div class="rx-field"><span class="rx-label">Age:</span> ${patientAge}</div>
      <hr style="border:0.5px solid #ccc;margin:12px 0;">
      <div class="rx-field"><span class="rx-label">Diagnosis:</span> ${diseases.length > 0 ? diseases.join(', ') : 'Not specified'}</div>
      <hr style="border:0.5px solid #ccc;margin:12px 0;">
      <div class="rx-field"><span class="rx-label">℞ Medicines:</span></div>
      <pre style="white-space:pre-wrap;font-family:inherit;padding:8px;background:#f9f9f9;border:1px solid #ddd;border-radius:6px;margin:4px 0 12px;">${medicines || 'None prescribed'}</pre>
      <div class="rx-field"><span class="rx-label">Treatment Plan:</span></div>
      <pre style="white-space:pre-wrap;font-family:inherit;padding:8px;background:#f9f9f9;border:1px solid #ddd;border-radius:6px;margin:4px 0 12px;">${treatment || 'None specified'}</pre>
      ${notes ? `<div class="rx-field"><span class="rx-label">Additional Notes:</span> ${notes}</div>` : ''}
      <br><br>
      <div style="text-align:right;margin-top:40px;border-top:1px solid #000;width:200px;margin-left:auto;padding-top:8px;">
        <span style="font-size:12px;">Doctor's Signature</span>
      </div>
      <p style="text-align:center;font-size:10px;color:#999;margin-top:24px;">© 2026 MH Connect Team — Maharashtra Health Connect</p>
    `;
    printArea.style.display = 'block';
    setTimeout(() => window.print(), 300);
  };

  //  ROLE-BASED TAB VISIBILITY 
  function initRoleTabs() {
    fetch('/api/session').then(r => r.json()).then(data => {
      if (!data.authenticated) return;
      const role = data.role || 'patient';
      // Doctor tab only visible to doctors
      document.querySelectorAll('[data-tab="doctor"]').forEach(el => {
        if (role !== 'doctor') el.style.display = 'none';
      });
      const doctorPanel = document.getElementById('tab-doctor');
      if (doctorPanel && role !== 'doctor') doctorPanel.style.display = 'none';
    }).catch(() => {});
  }

  //  INIT ALL 
  document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initViewToggle();
    initScrollProgress();
    initScrollTop();
    initCookieBanner();
    initPageLoader();
    initPwToggle();
    initMobileMenu();
    initSiteSearch();
    initRoleTabs();
  });
})();
