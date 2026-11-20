const firebaseConfig = { apiKey: "YOUR_FIREBASE_API_KEY", authDomain: "YOUR_PROJECT.firebaseapp.com", projectId: "YOUR_PROJECT", appId: "YOUR_APP_ID" };
const TURSO_URL = "https://shuvam-recondition-house-khemraj73-coder.aws-ap-south-1.turso.io";
const TURSO_TOKEN = "YOUR_TURSO_AUTH_TOKEN";
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider, OAuthProvider, signInWithPhoneNumber, RecaptchaVerifier, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();
const appleProvider = new OAuthProvider("apple.com");
const $ = (s) => document.querySelector(s);
const authScreen = $("#auth"), main = $("#main"), msg = $("#auth-msg");
const pageBody = $("#page-body"), pageTitle = $("#page-title");
function showMsg(t, ok=false){ msg.textContent=t; msg.style.color = ok?"#006C4C":"#B3261E"; }
onAuthStateChanged(auth, async (user) => {
  if (user) { authScreen.classList.add("hidden"); main.classList.remove("hidden"); await syncFromCloud(user.uid); renderPage("dash"); }
  else { main.classList.add("hidden"); authScreen.classList.remove("hidden"); }
});
$("#btn-login").onclick = async () => { try { await signInWithEmailAndPassword(auth, $("#email").value, $("#password").value); } catch (e) { showMsg(e.message); } };
$("#btn-register").onclick = async () => { try { await createUserWithEmailAndPassword(auth, $("#email").value, $("#password").value); showMsg("Registered", true); } catch (e) { showMsg(e.message); } };
$("#btn-google").onclick = async () => { try { await signInWithPopup(auth, googleProvider); } catch(e){ showMsg(e.message);} };
$("#btn-apple").onclick = async () => { try { await signInWithPopup(auth, appleProvider); } catch(e){ showMsg(e.message);} };
$("#btn-phone").onclick = async () => { try { if (!window.recaptchaVerifier) window.recaptchaVerifier = new RecaptchaVerifier(auth, "btn-phone", {size:"invisible"}); const r = await signInWithPhoneNumber(auth, $("#phone").value, window.recaptchaVerifier); window.confirmationResult = r; showMsg("OTP sent", true); } catch(e){ showMsg(e.message); } };
$("#btn-verify").onclick = async () => { try { await window.confirmationResult.confirm($("#otp").value); showMsg("Verified", true); } catch(e){ showMsg(e.message); } };
$("#btn-logout").onclick = () => signOut(auth);
document.querySelectorAll(".nav-item").forEach(b => b.onclick = () => { document.querySelectorAll(".nav-item").forEach(x=>x.classList.remove("active")); b.classList.add("active"); renderPage(b.dataset.page); });
function renderPage(p) { const titles = {dash:"Dashboard",bike:"Bike",saman:"Saman",hisab:"Hisab",bills:"Bills",settings:"Settings"}; pageTitle.textContent = titles[p] || p; pageBody.innerHTML = ""; if (p === "dash") { pageBody.innerHTML = `<div class="card"><h3>Today's Sales</h3><div class="value" id="k1">—</div></div><div class="card"><h3>This Month</h3><div class="value" id="k2">—</div></div><div class="card"><h3>Pending Due</h3><div class="value" id="k3">—</div></div><div class="card"><h3>Stock Bikes</h3><div class="value" id="k4">—</div></div>`; } else { pageBody.innerHTML = `<div class="card"><h3>${titles[p]}</h3><p>Module ready.</p></div>`; } }
async function turso(sql, args=[]) { const res = await fetch(TURSO_URL + "/v2/pipeline", { method:"POST", headers:{"Authorization":"Bearer "+TURSO_TOKEN,"Content-Type":"application/json"}, body: JSON.stringify({requests:[{type:"execute",stmt:{sql,args:args.map(v=>({type:"text",value:String(v)}))}}]}) }); const data = await res.json(); return data.results?.[0]?.response?.result; }
async function syncFromCloud(uid) { try { await turso("SELECT 1"); } catch (e) { console.warn("sync failed", e); } }
const ts = $("#theme-select"); ["midnight","ocean","emerald","sunset","pearl"].forEach(t=>{ const o=document.createElement("option"); o.value=t; o.textContent=t; ts.appendChild(o); }); ts.onchange = () => document.documentElement.dataset.theme = ts.value; document.documentElement.dataset.theme = "midnight";
