/* Maharashtra Health Connect — Login JS | (c) 2026 Akansh Shaw */
(async function(){
  try{const r=await fetch('/api/session');const d=await r.json();if(d.authenticated)window.location.href='/';}catch(e){}
})();

function switchTab(t){
  document.getElementById('tab-login').classList.toggle('active',t==='login');
  document.getElementById('tab-register').classList.toggle('active',t==='register');
  document.getElementById('login-form').classList.toggle('active',t==='login');
  document.getElementById('register-form').classList.toggle('active',t==='register');
  document.getElementById('login-error').textContent='';
  document.getElementById('register-error').textContent='';
}

function togglePw(id,btn){
  const inp=document.getElementById(id);
  const icon=btn.querySelector('i');
  inp.type=inp.type==='password'?'text':'password';
  icon.className=inp.type==='password'?'fas fa-eye':'fas fa-eye-slash';
}

async function handleLogin(e){
  e.preventDefault();
  const btn=document.getElementById('login-btn');
  const err=document.getElementById('login-error');
  err.textContent='';
  btn.disabled=true;
  btn.innerHTML='<i class="fas fa-spinner fa-spin"></i> Signing in...';
  try{
    const res=await fetch('/api/login',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        username:document.getElementById('login-username').value.trim(),
        password:document.getElementById('login-password').value,
        remember:document.getElementById('login-remember').checked
      })
    });
    const data=await res.json();
    if(res.ok&&data.success){
      btn.innerHTML='<i class="fas fa-check"></i> Success!';
      btn.style.background='linear-gradient(135deg,#059669,#34d399)';
      setTimeout(()=>window.location.href='/',500);
    }else{
      err.innerHTML='<i class="fas fa-exclamation-circle"></i> '+(data.error||'Login failed');
      btn.disabled=false;
      btn.innerHTML='<span>Sign In</span><i class="fas fa-arrow-right"></i>';
    }
  }catch(ex){
    err.innerHTML='<i class="fas fa-exclamation-circle"></i> Connection error';
    btn.disabled=false;
    btn.innerHTML='<span>Sign In</span><i class="fas fa-arrow-right"></i>';
  }
}

async function handleRegister(e){
  e.preventDefault();
  const btn=document.getElementById('register-btn');
  const err=document.getElementById('register-error');
  err.textContent='';
  btn.disabled=true;
  btn.innerHTML='<i class="fas fa-spinner fa-spin"></i> Creating...';
  try{
    const res=await fetch('/api/register',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        name:document.getElementById('reg-name').value.trim(),
        email:document.getElementById('reg-email').value.trim(),
        username:document.getElementById('reg-username').value.trim(),
        password:document.getElementById('reg-password').value,
        remember:document.getElementById('reg-remember').checked
      })
    });
    const data=await res.json();
    if(res.ok&&data.success){
      btn.innerHTML='<i class="fas fa-check"></i> Account Created!';
      btn.style.background='linear-gradient(135deg,#059669,#34d399)';
      setTimeout(()=>window.location.href='/',500);
    }else{
      err.innerHTML='<i class="fas fa-exclamation-circle"></i> '+(data.error||'Registration failed');
      btn.disabled=false;
      btn.innerHTML='<span>Create Account</span><i class="fas fa-user-plus"></i>';
    }
  }catch(ex){
    err.innerHTML='<i class="fas fa-exclamation-circle"></i> Connection error';
    btn.disabled=false;
    btn.innerHTML='<span>Create Account</span><i class="fas fa-user-plus"></i>';
  }
}
