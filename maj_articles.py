#!/usr/bin/env python3
"""
Met à jour les pages d'articles du blog (menu, pied de page, CSS, JSON-LD).

Usage, depuis la racine de votre dépôt :
  python3 maj_articles.py blog            # simulation : affiche ce qui changerait
  python3 maj_articles.py blog --apply    # applique les modifications

Le script traite blog/*.html sauf index*.html. Il est sans danger si on le relance
(les fichiers déjà à jour sont ignorés). Vérifiez ensuite avec : git diff
"""
import re, sys, json, glob, os

MARK = "/* maj-2026 */"

NAV = '''<ul id="navList">
      <li><a class="navlink" href="/cas-clients">Cas clients</a></li>
      <li><a class="navlink" href="/#methode">Méthode</a></li>
      <li><a class="navlink" href="/blog/" aria-current="page" style="color:var(--accent);">Blog</a></li>
      <li><a class="navlink" href="/apropos">À propos</a></li>
      <li><a class="btn btn-primary nav-cta" href="/#contact">Me contacter</a></li>
    </ul>'''

FOOTER = '''<footer class="site" id="contact">
  <div class="footer-head">
    <div>
      <h2>Travaillons ensemble.</h2>
      <p class="lede">Un projet de contenu SEO, un audit technique ou une refonte éditoriale ? Écrivez-moi, je réponds sous 24h.</p>
      <div class="footer-links">
        <a class="btn btn-ghost" href="https://www.linkedin.com/in/herinirina-beranto-4b4932333" target="_blank" rel="noopener">LinkedIn</a>
      </div>
      <p class="contact-direct">
        <a href="mailto:herinirinaberanto@gmail.com">herinirinaberanto@gmail.com</a>
        <button class="copy-btn" id="copyEmail" type="button">copier</button><br>
        <a href="tel:+261342375859">+261 34 23 758 59</a> · Antananarivo, Madagascar
      </p>
    </div>
    <form class="contact" id="contactForm" method="POST" action="https://formspree.io/f/xnpjywpw">
      <input type="text" name="_gotcha" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label>Nom<input type="text" name="nom" required autocomplete="name"></label>
      <label>Email<input type="email" name="email" required autocomplete="email"></label>
      <label>Type de projet
        <select name="projet">
          <option>Rédaction SEO</option>
          <option>Audit technique</option>
          <option>Stratégie éditoriale</option>
          <option>Autre</option>
        </select>
      </label>
      <label>Message<textarea name="message" required></textarea></label>
      <button class="btn btn-primary" type="submit">Envoyer le message</button>
      <p id="formStatus" role="status" style="font-size:0.9rem;color:#8FD6B8;margin:0;"></p>
    </form>
  </div>
  <div class="footer-bottom">
    <p>© 2026 Herinirina Beranto Rafalinjanahary</p>
    <div class="badges"><span class="chip">Disponible en freelance</span></div>
  </div>
</footer>'''

FORM_JS = '''<script>
(function(){
  var f=document.getElementById('contactForm'),st=document.getElementById('formStatus');
  if(!f)return;
  f.addEventListener('submit',function(e){
    e.preventDefault();
    st.textContent='Envoi en cours...';
    fetch(f.action,{method:'POST',body:new FormData(f),headers:{'Accept':'application/json'}})
      .then(function(r){
        if(r.ok){f.reset();st.textContent='Merci, votre message est envoyé. Je vous réponds sous 24h.';}
        else{st.textContent="L'envoi a échoué. Écrivez-moi directement par email.";}
      })
      .catch(function(){st.textContent="L'envoi a échoué. Écrivez-moi directement par email.";});
  });
})();
</script>
'''

CSS = MARK + '''
.btn{font-family:var(--body);cursor:pointer;justify-content:center;}
.btn-primary{background:var(--ink);color:#fff;}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(20,33,43,0.18);}
.nav ul{align-items:center;}
.nav-cta{padding:9px 16px;font-size:0.85rem;}
footer.site .lede{margin-bottom:22px;}
.footer-links{display:flex;gap:12px;flex-wrap:wrap;}
.footer-links .btn-ghost{border-color:rgba(255,255,255,0.25);color:#fff;}
.contact-direct{margin-top:26px;font-family:var(--mono);font-size:0.85rem;color:#AEBAB8;}
.contact-direct a{color:#fff;text-decoration:none;}
.contact-direct a:hover{color:#8FD6B8;}
.copy-btn{color:#AEBAB8;font-size:0.75rem;}
form.contact{display:flex;flex-direction:column;gap:14px;}
form.contact label{font-family:var(--mono);font-size:0.75rem;color:#AEBAB8;display:flex;flex-direction:column;gap:6px;}
form.contact input,form.contact textarea,form.contact select{font:inherit;font-family:var(--body);font-size:0.95rem;color:#fff;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.18);border-radius:8px;padding:11px 13px;}
form.contact select option{color:#14212B;}
form.contact textarea{min-height:110px;resize:vertical;}
form.contact .btn-primary{background:#fff;color:var(--ink);align-self:flex-start;}
.hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0;}
.footer-bottom p{color:#9DAEA6;}
@media (max-width:860px){
  .nav ul{position:absolute;top:100%;}
  .nav-cta{margin:14px 28px;}
  .nav-toggle{width:40px;height:40px;font-size:1.1rem;color:var(--ink);}
}
'''

MONTHS = {m:i+1 for i,m in enumerate("janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split())}

def iso(txt):
    m = re.search(r'(\d{1,2})\s+([a-zéû]+)\s+(\d{4})', txt)
    if m and m.group(2) in MONTHS:
        return "%s-%02d-%02d" % (m.group(3), MONTHS[m.group(2)], int(m.group(1)))

def jsonld(html):
    g = lambda p: (re.search(p, html, re.S) or [None, None])[1]
    title = re.sub(r'<[^>]+>', '', g(r'<h1[^>]*>(.*?)</h1>') or '').strip()
    desc = g(r'<meta name="description" content="([^"]*)"')
    url = g(r'<link rel="canonical" href="([^"]*)"')
    img = g(r'<meta property="og:image" content="([^"]*)"')
    meta = g(r'<span class="meta">(.*?)</span>') or ''
    parts = meta.split('Mis à jour')
    pub = iso(parts[0]); mod = iso(parts[1]) if len(parts) > 1 else None
    if not (title and url and pub): return None
    d = {"@context":"https://schema.org","@type":"BlogPosting","headline":title,
         "description":desc,"image":img,"mainEntityOfPage":url,"datePublished":pub,
         "dateModified":mod or pub,"inLanguage":"fr",
         "author":{"@type":"Person","name":"Herinirina Beranto Rafalinjanahary","url":"https://beranto-seo.com/apropos"},
         "publisher":{"@type":"Person","name":"Herinirina Beranto Rafalinjanahary","url":"https://beranto-seo.com/"}}
    return '<script type="application/ld+json">\n' + json.dumps(d, ensure_ascii=False, indent=1) + '\n</script>\n'

def patch(html):
    if MARK in html:
        return html, ["déjà à jour"]
    log = []
    def sub(pat, rep, label, flags=re.S, count=1):
        nonlocal html
        new, n = re.subn(pat, lambda m: rep if isinstance(rep, str) else rep(m), html, count=count, flags=flags)
        if n: html = new; log.append(label)
        else: log.append("ATTENTION : introuvable : " + label)
    sub(r'<ul id="navList">.*?</ul>', NAV, "menu")
    sub(r'<footer class="site" id="contact">.*?</footer>', FOOTER, "pied de page")
    sub(r'</style>', CSS + '</style>', "CSS")
    html = html.replace('--ink-faint:#8A9BA4', '--ink-faint:#66777F')
    sub(r'(<img src="/images/Beranto-Logo-Vector\.svg"[^>]*?)(\s*class="brand-logo">)',
        lambda m: m.group(1) + ' width="36" height="36"' + m.group(2) if 'width=' not in m.group(1) else m.group(0), "logo width/height")
    sub(r'(<a [^>]*href=")https://beranto-seo\.com/', r'\1/', "liens internes relatifs", count=0)
    html = html.replace('loading="eager">', 'fetchpriority="high">')
    if 'application/ld+json' not in html:
        ld = jsonld(html)
        if ld: html = html.replace('</head>', ld + '</head>', 1); log.append("JSON-LD BlogPosting")
        else: log.append("ATTENTION : JSON-LD non généré (titre, canonical ou date introuvable)")
    if 'id="contactForm"' in html and 'getElementById(\'contactForm\')' not in html:
        html = html.replace('</body>', FORM_JS + '</body>', 1); log.append("script formulaire")
    return html, log

def main():
    if len(sys.argv) < 2: print(__doc__); return
    folder = sys.argv[1]; apply = '--apply' in sys.argv
    files = [f for f in sorted(glob.glob(os.path.join(folder, '*.html'))) if not os.path.basename(f).startswith('index')]
    for f in files:
        src = open(f, encoding='utf-8').read()
        out, log = patch(src)
        print(f, '->', '; '.join(log))
        if apply and out != src:
            open(f, 'w', encoding='utf-8').write(out)
    print('\n' + ('Modifications appliquées.' if apply else 'Simulation terminée. Relancez avec --apply pour écrire les fichiers.'))

if __name__ == '__main__':
    main()
