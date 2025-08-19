(function(){
  const $ = (sel, root=document) => root.querySelector(sel);
  const $$ = (sel, root=document) => [...root.querySelectorAll(sel)];

  // --- Add to cart (AJAX) ---
  function bindAddForms(){
    $$(".add-form").forEach(form=>{
      form.addEventListener("submit", async (e)=>{
        e.preventDefault();
        const fd = new FormData(form);
        if (!fd.get("qty")) fd.set("qty","1");
        const res = await fetch(CANGROO.addToCartUrl, {method:"POST", body:fd});
        const data = await res.json();
        if(data.ok){
          $("#cart-count").textContent = data.cart_count;
          toast(data.message);
        }else{
          toast("Could not add to cart", true);
        }
      });
    });
  }

  // --- Cart interactions ---
  function bindCart(){
    $$(".qty-input").forEach(inp=>{
      inp.addEventListener("change", async (e)=>{
        const pid = inp.dataset.pid;
        const qty = Math.max(1, parseInt(inp.value || "1",10));
        const fd = new FormData(); fd.set("pid", pid); fd.set("qty", String(qty));
        const res = await fetch(CANGROO.updateCartUrl, {method:"POST", body:fd});
        const data = await res.json();
        if(data.ok){
          $("#cart-count").textContent = data.cart_count;
          updateSummary(data.summary);
          // update row line total visually (price * qty)
          const row = inp.closest(".cart-row");
          const price = parseFloat(row.querySelector(".ci-price").textContent.replace("$",""));
          row.querySelector(".ci-total").textContent = "$ " + (price*qty).toFixed(2);
        }
      });
    });

    $$(".remove-btn").forEach(btn=>{
      btn.addEventListener("click", async ()=>{
        const pid = btn.dataset.pid;
        const fd = new FormData(); fd.set("pid", pid);
        const res = await fetch(CANGROO.removeUrl, {method:"POST", body:fd});
        const data = await res.json();
        if(data.ok){
          $("#cart-count").textContent = data.cart_count;
          const row = btn.closest(".cart-row");
          row.remove();
          // recompute by requesting update with qty=0 (already removed) to refresh totals quickly
          const res2 = await fetch(CANGROO.updateCartUrl, {method:"POST", body:(() => { const f=new FormData(); f.set("pid","_"); f.set("qty","1"); return f; })()});
          const data2 = await res2.json().catch(()=>null);
          if(data2 && data2.summary) updateSummary(data2.summary);
          toast("Removed from cart");
          if ($$(".cart-row").length === 0) location.reload();
        }
      });
    });
  }

  function updateSummary(sum){
    if(!sum) return;
    const map = { "sum-sub": "subtotal", "sum-ship":"shipping", "sum-tax":"tax", "sum-total":"total" };
    Object.entries(map).forEach(([id,key])=>{
      const el = document.getElementById(id);
      if(el) el.textContent = "$ " + (sum[key] ?? "");
    });
  }

  // --- Search suggestions ---
  function bindSearch(){
    const input = $("#q"); if(!input) return;
    const wrap = $("#search-suggest");
    let aborter = null;

    input.addEventListener("input", async ()=>{
      const q = input.value.trim();
      if(q.length < 2){ wrap.hidden = true; wrap.innerHTML = ""; return; }
      try{
        aborter?.abort();
        aborter = new AbortController();
        const res = await fetch(CANGROO.searchUrl + "?q=" + encodeURIComponent(q), {signal: aborter.signal});
        const items = await res.json();
        if(!items.length){ wrap.hidden = true; wrap.innerHTML=""; return; }
        wrap.innerHTML = items.map(it => `
          <a href="/product/${it.id}">
            <img src="${it.image}" alt="">
            <div>
              <div style="font-weight:700">${it.name}</div>
              <small class="muted">$ ${it.price.toFixed(2)}</small>
            </div>
            <span class="btn" style="pointer-events:none">$ ${it.price.toFixed(2)}</span>
          </a>
        `).join("");
        wrap.hidden = false;
      }catch(e){}
    });

    document.addEventListener("click", (e)=>{
      if(!wrap.contains(e.target) && e.target !== input){
        wrap.hidden = true;
      }
    });
  }

  // --- Tiny toast ---
  function toast(msg, danger=false){
    let el = document.createElement("div");
    el.className = "toast";
    el.textContent = msg;
    el.style.cssText = `
      position: fixed; bottom: 18px; left: 50%; transform: translateX(-50%);
      background: ${danger ? "#350914" : "#0b2d20"};
      border: 1px solid ${danger ? "#ff5577" : "#00c265"};
      color: ${danger ? "#ffb3c2" : "#97ffd7"};
      padding: .6rem .9rem; border-radius: .6rem; z-index: 50;
      box-shadow: 0 10px 30px #0009; font-weight:700;
    `;
    document.body.appendChild(el);
    setTimeout(()=>{ el.style.opacity="0"; el.style.transition="opacity .5s"; }, 1500);
    setTimeout(()=>{ el.remove(); }, 2100);
  }

  // init
  document.addEventListener("DOMContentLoaded", ()=>{
    bindAddForms();
    bindCart();
    bindSearch();
  });
})();