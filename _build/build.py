#!/usr/bin/env python3
"""Kratz Family Chiropractic preview builder (Grove family layout, GrowGonstead page set).
Catalog copy is read from localember/localember tools/bd-generator/catalog.
Run: python3 _build/build.py  (writes into ./site)"""
import json, os, re, html, sys, datetime
HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.dirname(HERE)  # repo root
CAT=os.environ.get('LE_CATALOG','/workspace/le/tools/bd-generator/catalog')
BASE='/kratz-chiro-preview'
ORIGIN='https://localember.github.io'
SITE=ORIGIN+BASE+'/'
E=html.escape

B={ 'name':'Kratz Family Chiropractic','short':'Kratz Family Chiropractic',
  'doctor':'Dr. Doug Kratz','doctor_full':'Dr. Douglas Kratz, D.C.','doc_short':'Dr. Kratz',
  'street':'600 Pleasant Oak Dr, Suite B','city':'Oregon','state':'WI','zip':'53575',
  'phone':'(608) 291-1037','tel':'+16082911037',
  'lat':'42.911667','lng':'-89.374365',
  'facebook':'https://www.facebook.com/people/Kratz-Family-Chiropractic/61596698663855/',
  'towns':'Oregon, Stoughton, Fitchburg, Brooklyn and the south Madison area',
  'lead_email':'doug@kratzfamilychiro.com'}
B['addr_full']=f"{B['street']}, {B['city']}, {B['state']} {B['zip']}"
MAPS_RAW='https://www.google.com/maps/dir/?api=1&destination=Kratz+Family+Chiropractic,+600+Pleasant+Oak+Dr+Suite+B,+Oregon,+WI+53575&destination_place_id=ChIJEWOaEgBLBogRoEu8i9XBYqw'
MAPS=MAPS_RAW.replace('&','&amp;')
GBP_URL='https://maps.google.com/?cid=12421703845157817248'
EMBED='https://maps.google.com/maps?q=Kratz+Family+Chiropractic%2C+600+Pleasant+Oak+Dr+Suite+B%2C+Oregon%2C+WI+53575&amp;z=15&amp;output=embed'
# Google Business Profile hours (Google Maps listing, read 2026-11-19)
HOURS=[('Monday','09:00','18:00'),('Tuesday','09:00','12:00'),('Wednesday','14:00','18:00'),('Thursday','14:00','18:00'),('Friday','09:00','12:00'),('Saturday',None,None),('Sunday',None,None)]
def t12(t):
    h,m=map(int,t.split(':')); s='am' if h<12 else 'pm'; h=h%12 or 12
    return f"{h}:{m:02d} {s}"
def hours_txt(d):
    return 'Closed' if not d[1] else f"{t12(d[1])} to {t12(d[2])}"
TOK={'city':B['city'],'state':B['state'],'clinic_name':B['name'],'service_towns':B['towns'],'phone':B['phone'],'street':B['street']}
def sub(s):
    if not isinstance(s,str): return s
    def r(m):
        k=m.group(1); d=None
        if '|' in k: k,d=k.split('|',1)
        return TOK.get(k, d if d is not None else m.group(0))
    s=re.sub(r'\{\{([^}]+)\}\}',r,s)
    return s
def U(p): return BASE+p

SERVICES=['chiropractic','pediatric','prenatal','wellness-care','massage-therapy','nutrition','supplementation']
CONDITIONS=['back-pain','neck-pain','headaches','sciatica','disc-injury','whiplash','shoulder-pain','hip-pain','knee-pain','sports-injury','work-injury','scoliosis','arthritis']
GONSTEAD=['gonstead-system','founder-of-gonstead','first-visit','second-visit','follow-up-visit']
def load(kind,slug): return json.load(open(f'{CAT}/{kind}/{slug}.json'))
SVC={s:load('services',s) for s in SERVICES}
CON={s:load('conditions',s) for s in CONDITIONS}
GON={s:load('gonstead',s) for s in GONSTEAD}
FAQG=json.load(open(f'{CAT}/faq-general.json'))

# ---------- Dr. Kratz answers, Nov 23 2026 (ticket KFC-2026-11-23-preview-answers) ----------
# Catalog files stay the base. These are preview-only overrides applied at build time; nothing here is written back to the catalog.
INS='We have plans available for all kinds of insurance.'
NP_SPECIAL='$87.00'
FIRST_MIN='30 minutes'
CTA_LABEL='Claim $87 New Patient Special'
CTA_HREF='/request-appointment/'
HOME_SERVICES=['chiropractic','pediatric','prenatal','wellness-care','massage-therapy','nutrition']  # original homepage set; supplementation stays on /services/ and in the nav
# Testimonials and bio: word for word from Dr. Kratz (double spaces and missing periods kept). Never edit.
TESTIMONIALS=[
 ('"Kratz Family Chiropractic has been a part of my life for over 20 years.  Dr Kratz takes the time to listen to my questions and concerns and then helps to coordinate a plan addressing my individual needs"','Kelly, Janesville'),
 ('"I have been going to Kratz Family Chiropractic for over 25 years.  I can\'t imagine getting the care that I receive anywhere else"','Ann, Oregon'),
 ('"Over the past 20 years Dr. Doug has seen me through knee, shoulder and acute ankle issues. I know that he can be counted on to help with any joint problem."','Karen, Madison')]
BIO=['Dr. Doug Kratz received his Chiropractic degree from Palmer College of Chiropractic in Davenport Iowa.  He has received extensive advanced training in the Gonstead technique and utilizes it almost exclusively.  Along with his education, he has over 25 years of clinical experience.',
 'His patient centered approach is one that is focused on helping his patients achieve optimal physical, mental and social well-being.',
 'When he is not helping patients, Dr. Kratz enjoys paddling, fishing and backpacking.  He is also the proud grandfather of two beautiful grandchildren.']
VERB='style="white-space:pre-wrap"'  # keeps the double spaces visible
def bio_html(): return ''.join(f'<p {VERB}>{E(p)}</p>' for p in BIO)
def tcards(): return ''.join(f'<div class="tcard"><p {VERB}>{E(q)}</p><p class="who">{E(w)}</p></div>' for q,w in TESTIMONIALS)
def offer_html(extra=''):
    return f'<div class="np-offer{extra}"><p><strong>New Patient special: {NP_SPECIAL}</strong></p><p>Your first visit takes about {FIRST_MIN}.</p><p>{INS}</p></div>'

def _walk(o,fn):
    if isinstance(o,dict):
        for k in list(o): o[k]=_walk(o[k],fn)
    elif isinstance(o,list):
        for i in range(len(o)): o[i]=_walk(o[i],fn)
    elif isinstance(o,str): return fn(o)
    return o
ALLCAT=[SVC,CON,GON,FAQG]
def R(old,new,objs=None,regex=False):
    hits=[0]
    def fn(s):
        n=len(re.findall(old,s)) if regex else s.count(old)
        if n: hits[0]+=n; return re.sub(old,new,s) if regex else s.replace(old,new)
        return s
    for o in (objs if objs is not None else ALLCAT): _walk(o,fn)
    if not hits[0]: raise SystemExit('override did not match: '+old)
def drop(lst,pred,what):
    n=len(lst); lst[:]=[x for x in lst if not pred(x)]
    if len(lst)==n: raise SystemExit('drop did not match: '+what)

# first visit: 30 minutes, no online intake forms. X-ray copy is kept (Brevin, Nov 23 2026 5:15 PM CT).
fv=GON['first-visit']
R('Around 45 minutes to an hour, and you will leave','About 30 minutes, and you will leave',[fv])
R('Around 45 minutes to an hour: your history, a full five-component analysis, imaging where appropriate, and usually your first adjustment.','About 30 minutes: your history, a full five-component analysis, imaging where appropriate, and usually your first adjustment.',[fv])
for b in fv['blocks']:
    if b.get('type')=='timeline':
        for it in b['items']:
            if 'intake forms online' in it.get('body',''):
                it['title']='Your history'
                it['body']='We go through your history in the office, so the time is spent on your spine and on what brought you in.'
R('Allow up to an hour so nothing is rushed.','Allow about 30 minutes so nothing is rushed.',[fv])
fv['meta']=['⏱ Allow about 30 minutes','📍 Serving {{service_towns}}']
# nutrition page: rework the "without fads or supplements" phrasing only; the office offers Supplementation.
R('Straightforward nutrition guidance for energy and recovery, without fads or supplements.','Straightforward nutrition guidance for energy and recovery, without fads.',[SVC['nutrition']])
R('without fads or a cupboard full of supplements.','without fads.',[SVC['nutrition']])
# supplementation page: use a dedicated supplements photo, not the nutrition food image
SVC['supplementation']['hero']['image']='Catalog/Services/supplementation.svg'
SVC['supplementation']['hero']['alt']='Supplement bottles and capsules on a table'
sv=GON['second-visit']
# insurance: the one line Dr. Kratz gave replaces coverage wording
R('Payment options are discussed at this visit, and if you have insurance and intend to claim, we provide the documentation you need to do it.','Payment options are discussed at this visit. '+INS,[sv])
R(' or what your insurance will cover','')
R(r'every plan and every (\w+) is different',r'every \1 is different',regex=True)
R('We cannot promise a specific outcome, what your insurance will cover, or how a claim will be decided; that sits with your insurer and your attorney if you have one.','We cannot promise a specific outcome or how a claim will be decided.',[CON['whiplash']])
R('We cannot promise a specific outcome, or what any insurer will cover and how they will decide it; that sits with them and, if you have one, your attorney.','We cannot promise a specific outcome or how a claim will be decided.',[CON['work-injury']])
R('Wellness visits are usually out of pocket, and we tell you the numbers before anything begins.','We tell you the numbers before anything begins.',[SVC['wellness-care']])
R('Coverage varies a lot by plan, so we go over the numbers with you up front.',INS+' We go over the numbers with you up front.',[FAQG])
INS_RE=re.compile(r'insur|plan\b|cover|workers|\bbill',re.I)
for D in (SVC,CON):
    for slug,d in D.items():
        bl=d['blocks']
        for i,b in enumerate(bl):
            if b['type']=='h2' and 'insurance' in b['text'].lower():
                p=bl[i+1]; assert p['type']=='p',slug
                keep=[s for s in re.split(r'(?<=[.!?])\s+',p['text']) if not INS_RE.search(s)]
                p['text']=' '.join([INS]+keep).replace('No referral is needed either way,','No referral is needed,')
            if b['type']=='costbox': b['items']=[x for x in b['items'] if not re.search(r'insurance|covered',x if isinstance(x,str) else x.get('text',''),re.I)]
        for f in d.get('faqs',[]):
            if f['q']=='Will my insurance cover it?': f['a']=INS+' We will always tell you the numbers up front so there are no surprises.'
NAV_NAMES={'chiropractic':'Gonstead Chiropractic Care','pediatric':'Chiropractic for Kids','prenatal':'Prenatal Chiropractic','wellness-care':'Wellness Care','massage-therapy':'Massage Therapy','nutrition':'Nutrition Support','supplementation':'Supplementation',
 'back-pain':'Back Pain','neck-pain':'Neck Pain','headaches':'Headaches & Migraines','sciatica':'Sciatica','disc-injury':'Disc Injury','whiplash':'Whiplash & Auto Injury','shoulder-pain':'Shoulder Pain','hip-pain':'Hip Pain','knee-pain':'Knee Pain','sports-injury':'Sports Injury','work-injury':'Work Injury','scoliosis':'Scoliosis','arthritis':'Arthritis',
 'gonstead-system':'5 Components of Gonstead','founder-of-gonstead':'Dr. Clarence Gonstead','first-visit':'First Visit','second-visit':'Second Visit','follow-up-visit':'Follow-Up Visits'}
IMG={}
def catimg(path):
    if not path: return None
    n=os.path.basename(path).replace(' ','-').replace('&','and').lower()
    if path.startswith('Gonstead/'): return 'images/'+n
    return 'images/catalog/'+n.replace('.webp','.jpg')
# related title -> slug
REL={'back pain':'back-pain','neck pain & tension':'neck-pain','neck pain':'neck-pain','headaches & migraines':'headaches','whiplash':'whiplash','shoulder pain':'shoulder-pain','sciatica & leg pain':'sciatica','sciatica':'sciatica','disc injury':'disc-injury','hip pain':'hip-pain','knee pain':'knee-pain','sports injury':'sports-injury','pediatric & kids':'pediatric','massage therapy':'massage-therapy','chiropractic care':'chiropractic','nutrition support':'nutrition','supplementation':'supplementation','pregnancy & postpartum':'prenatal','your first visit':'first-visit','your second visit':'second-visit','follow-up visits':'follow-up-visit','5 components of the gonstead technique':'gonstead-system','work injury':'work-injury','scoliosis':'scoliosis','arthritis':'arthritis'}
BUILT=set(SERVICES+CONDITIONS+GONSTEAD)
def rel_slug(it):
    s=it.get('slug') or (it.get('href') or '').strip('/') or REL.get(it['title'].lower())
    if s=='pregnancy': s='prenatal'
    return s if s in BUILT else None

# ---------- chrome ----------
def head(title,desc,path,schema,og_img='images/dr-kratz-portrait.jpg'):
    can=ORIGIN+U(path)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{E(title)}</title>
  <meta name="description" content="{E(desc)}">
  <link rel="canonical" href="{can}">
  <meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{can}"><meta property="og:image" content="{ORIGIN+U('/assets/'+og_img)}">
  <link rel="icon" href="{U('/assets/images/favicon-32.png')}" type="image/png" sizes="32x32">
  <link rel="icon" href="{U('/assets/images/favicon-192.png')}" type="image/png" sizes="192x192">
  <link rel="apple-touch-icon" href="{U('/assets/images/apple-touch-icon.png')}">
  <link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{U('/assets/styles.css')}">
  <script type="application/ld+json">{json.dumps(schema,indent=1,ensure_ascii=False)}</script>
</head>
'''
def navlink(slug,cur): 
    a=' aria-current="page"' if cur==f'/{slug}/' else ''
    return f'<li><a href="{U("/"+slug+"/")}"{a}>{E(NAV_NAMES[slug])}</a></li>'
def header(cur):
    col=lambda h,L:f'<div class="mega-col"><h3>{h}</h3><ul class="sub" style="display:block;padding:0">'+''.join(navlink(s,cur) for s in L)+'</ul></div>'
    return f'''<body>
<a class="skip" href="#main">Skip to content</a>
<div class="preview-banner">Design preview, not live <span>This site is not the live Kratz Family Chiropractic website and is hidden from search.</span></div>
<div class="topbar"><div class="wrap">
  <a href="{MAPS}" target="_blank" rel="noopener">{E(B['addr_full'])}</a>
  <div class="topbar-links"><a href="tel:{B['tel']}">Call {B['phone']}</a></div>
</div></div>
<header class="site-header"><div class="wrap header-inner">
  <a class="logo-link" href="{U('/')}"><img src="{U('/assets/images/logo-nav.png')}" width="640" height="178" alt="Kratz Family Chiropractic, Full Spine Gonstead Practitioner"></a>
  <span class="header-cta"><a class="btn btn--primary hdr-req" href="{U('/request-appointment/')}">{CTA_LABEL}</a> <a class="btn btn--primary hdr-call" href="tel:{B['tel']}">Call Now</a></span>
  <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
  <nav class="nav" id="site-nav" aria-label="Primary"><ul class="nav-list">
    <li class="nav-parent"><button type="button">Who We Are</button><ul class="sub"><li><a href="{U('/us/')}">Meet Dr. Kratz</a></li><li><a href="{U('/testimonials/')}">Testimonials</a></li></ul></li>
    <li class="nav-parent"><button type="button">Gonstead</button><ul class="sub">{navlink('gonstead-system',cur)}{navlink('founder-of-gonstead',cur)}</ul></li>
    <li class="nav-parent"><button type="button">New Patients</button><ul class="sub">{navlink('first-visit',cur)}{navlink('second-visit',cur)}{navlink('follow-up-visit',cur)}</ul></li>
    <li class="nav-parent"><button type="button">What We Do</button><div class="mega"><div class="mega-grid">
      {col('Services',SERVICES)}{col('Spine',['back-pain','neck-pain','headaches','sciatica','disc-injury'])}{col('Injuries',['whiplash','sports-injury','work-injury'])}{col('Joints and more',['shoulder-pain','hip-pain','knee-pain','scoliosis','arthritis'])}
    </div><p style="margin:.85rem 0 0;"><a href="{U('/services/')}">All services</a> &middot; <a href="{U('/conditions/')}">All conditions</a></p></div></li>
    <li><a href="{U('/faqs/')}">FAQ</a></li>
    <li><a href="{U('/contact-us/')}">Contact Us</a></li>
  </ul>
  <div class="nav-mobile-cta"><a class="btn btn--ghost" href="{U('/request-appointment/')}">{CTA_LABEL}</a> <a class="btn btn--primary" href="tel:{B['tel']}">Call {B['phone']}</a></div>
  </nav>
</div></header>
<main id="main">
'''
FB_SVG='<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7A10 10 0 0 0 22 12z"/></svg>'
def hours_list():
    return '<ul class="hours">'+''.join(f'<li><span>{d[0]}</span><span>{hours_txt(d)}</span></li>' for d in HOURS)+'</ul>'
def footer():
    yr=datetime.date.today().year
    legal=[('privacy-policy','Privacy Policy'),('terms-of-service','Terms of Service'),('healthcare-disclaimer','Healthcare Disclaimer'),('hipaa-privacy-practices','HIPAA Notice'),('good-faith-estimate','Good Faith Estimate'),('accessibility-statement','Accessibility'),('anti-discrimination','Anti-Discrimination')]
    return f'''</main>
<footer class="site-footer"><div class="wrap">
  <div class="foot-grid">
    <div>
      <img class="foot-logo-wide" src="{U('/assets/images/logo-white.png')}" width="640" height="178" alt="Kratz Family Chiropractic">
      <p class="nap" style="color:#fff">{E(B['street'])}<br>{B['city']}, {B['state']} {B['zip']}<br><a href="tel:{B['tel']}">{B['phone']}</a></p>
      <p class="foot-social"><a href="{B['facebook']}" target="_blank" rel="noopener" aria-label="Kratz Family Chiropractic on Facebook">{FB_SVG} Facebook</a></p>
    </div>
    <div><h3>Office hours</h3>{hours_list()}</div>
    <div><h3>Explore</h3><ul style="list-style:none;padding:0;margin:0;line-height:2">
      <li><a href="{U('/gonstead-system/')}">The Gonstead Technique</a></li><li><a href="{U('/first-visit/')}">Your First Visit</a></li><li><a href="{U('/services/')}">Services</a></li><li><a href="{U('/conditions/')}">Conditions</a></li><li><a href="{U('/us/')}">Meet Dr. Kratz</a></li><li><a href="{U('/request-appointment/')}">{CTA_LABEL}</a></li><li><a href="{U('/contact-us/')}">Contact Us</a></li></ul>
      <p style="margin-top:1rem"><a class="btn btn--white" href="tel:{B['tel']}">Call {B['phone']}</a></p></div>
  </div>
  <nav class="legal-nav" aria-label="Legal">{''.join(f'<a href="{U("/"+s+"/")}">{t}</a>' for s,t in legal)}</nav>
  <p class="copy">&copy; {yr} Kratz Family Chiropractic. Gonstead chiropractor in Oregon, WI. Design preview by Grow Gonstead.</p>
</div></footer>
<div class="mobile-bar"><a class="btn btn--primary" href="{U('/request-appointment/')}">{CTA_LABEL}</a><a class="btn btn--ghost" href="tel:{B['tel']}">Call</a></div>
<script src="{U('/assets/site.js')}" defer></script>
</body></html>
'''
# ---------- schema ----------
BIZ_ID=SITE+'#business'; DOC_ID=SITE+'us/#person'
def biz_schema():
    return {"@type":["Chiropractor","LocalBusiness"],"@id":BIZ_ID,"name":B['name'],"url":SITE,
      "logo":ORIGIN+U('/assets/images/logo.png'),"image":[ORIGIN+U('/assets/images/office-exterior.jpg'),ORIGIN+U('/assets/images/dr-kratz-portrait.jpg')],
      "telephone":B['tel'],"priceRange":"$$" if False else None,
      "address":{"@type":"PostalAddress","streetAddress":B['street'],"addressLocality":B['city'],"addressRegion":B['state'],"postalCode":B['zip'],"addressCountry":"US"},
      "geo":{"@type":"GeoCoordinates","latitude":B['lat'],"longitude":B['lng']},
      "hasMap":GBP_URL,
      "openingHoursSpecification":[{"@type":"OpeningHoursSpecification","dayOfWeek":d,"opens":o,"closes":c} for d,o,c in HOURS if o],
      "areaServed":[{"@type":"City","name":"Oregon, WI"},{"@type":"City","name":"Stoughton, WI"},{"@type":"City","name":"Fitchburg, WI"},{"@type":"City","name":"Brooklyn, WI"}],
      "medicalSpecialty":"Chiropractic","knowsAbout":["Gonstead technique","Full spine chiropractic","Family chiropractic care"],
      "sameAs":[B['facebook']],"employee":{"@id":DOC_ID}}
def person_schema():
    return {"@type":"Person","@id":DOC_ID,"name":"Dr. Douglas Kratz","alternateName":"Dr. Doug Kratz","honorificSuffix":"D.C.","jobTitle":"Chiropractor","description":"Chiropractor with 25 years in practice, owner of Kratz Family Chiropractic in Oregon, WI.","worksFor":{"@id":BIZ_ID},"image":ORIGIN+U('/assets/images/dr-kratz-portrait.jpg'),"url":SITE+'us/'}
def clean(o):
    if isinstance(o,dict): return {k:clean(v) for k,v in o.items() if v is not None}
    if isinstance(o,list): return [clean(v) for v in o]
    return o
def crumbs_schema(trail):
    return {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":ORIGIN+U(p)} for i,(n,p) in enumerate(trail)]}
def faq_schema(faqs):
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":sub(f['q']),"acceptedAnswer":{"@type":"Answer","text":sub(f['a'])}} for f in faqs]}
def graph(*items): return clean({"@context":"https://schema.org","@graph":[i for i in items if i]})
def webpage(path,name,desc,typ="WebPage",about=None):
    d={"@type":typ,"@id":ORIGIN+U(path)+'#webpage',"url":ORIGIN+U(path),"name":name,"description":desc,"isPartOf":{"@type":"WebSite","name":B['name'],"url":SITE},"inLanguage":"en-US"}
    d["about"]=about or {"@id":BIZ_ID}
    return d
def crumbs_html(trail):
    parts=[]
    for i,(n,p) in enumerate(trail):
        parts.append(f'<span>{E(n)}</span>' if i==len(trail)-1 else f'<a href="{U(p)}">{E(n)}</a>')
    return '<div class="crumb-wrap"><div class="wrap" style="padding-top:1rem"><nav class="crumbs" aria-label="Breadcrumb">'+' / '.join(parts)+'</nav></div></div>'

# ---------- catalog blocks ----------
def slugify(t): return re.sub(r'[^a-z0-9]+','-',t.lower()).strip('-')
def bullets(items):
    out=[]
    for i in items:
        if isinstance(i,dict):
            if i.get('requires') and i['requires'] not in BUILT: continue
            i=i['text']
        out.append(f'<li>{E(sub(i))}</li>')
    return '<ul>'+''.join(out)+'</ul>'
def blocks(bl):
    o=[]
    for b in bl:
        t=b['type']
        if t=='answer': o.append(f'<div class="answer"><span class="lbl">{E(b.get("label","The short answer"))}</span><p>{E(sub(b["text"]))}</p></div>')
        elif t=='lede': o.append(f'<p class="lede">{E(sub(b["text"]))}</p>')
        elif t=='h2': tx=sub(b['text']); o.append(f'<h2 class="h2" id="{slugify(tx)}">{E(tx)}</h2>')
        elif t=='p': o.append(f'<p>{E(sub(b["text"]))}</p>')
        elif t=='bullets': o.append(bullets(b['items']))
        elif t=='costbox':
            o.append(f'<div class="costbox"><strong>{E(b.get("label","Cost and insurance"))}</strong>{bullets(b["items"])}<p class="note">{E(sub(b.get("note","")))}</p></div>')
        elif t=='citation':
            o.append(f'<div class="citation"><strong>{E(sub(b["stat"]))}</strong>{E(sub(b["text"]))} <span>{E(sub(b.get("source","")))}<a href="{E(b["link_url"])}" target="_blank" rel="noopener">{E(b.get("link_text","Source"))}</a></span></div>')
        elif t=='timeline':
            o.append('<ol class="timeline">'+''.join(f'<li><h3>{E(sub(i["title"]))}</h3><p>{E(sub(i.get("body","")))}</p></li>' for i in b['items'])+'</ol>')
        elif t=='quote':
            o.append(f'<blockquote class="pullquote">{E(sub(b["text"]))}<cite>{E(b["attribution"])}</cite></blockquote>')
        elif t=='image':
            o.append(f'<figure class="catalog-fig"><img src="{U("/assets/"+catimg(b["src"]))}" alt="{E(sub(b["alt"]))}" loading="lazy"></figure>')
        elif t=='columns':
            o.append('<div class="card-grid">'+''.join(f'<div class="costbox"><strong>{E(c["label"])}</strong>{bullets(c["items"])}</div>' for c in (b['left'],b['right']))+'</div>')
        else: raise SystemExit('unknown block '+t)
    return ''.join(o)
def faq_html(faqs,heading='Common questions'):
    if not faqs: return ''
    return f'<section class="band band--mist"><div class="wrap"><h2>{E(sub(heading))}</h2><div class="faq prose prose--wide">'+''.join(f'<details><summary>{E(sub(f["q"]))}</summary><p>{E(sub(f["a"]))}</p></details>' for f in faqs)+'</div></div></section>'
def cta_band(h='Ready to come in?',s=None):
    s=s or f'Call the office to book a first visit with {B["doc_short"]} in Oregon, or send a request and we will call you back.'
    return f'''<section class="band band--forest cta-band"><div class="wrap"><h2>{E(sub(h))}</h2><p>{E(sub(s))}</p><p class="btn-row" style="justify-content:center"><a class="btn btn--white" href="tel:{B['tel']}">Call {B['phone']}</a> <a class="btn btn--ghost" href="{U('/request-appointment/')}">{CTA_LABEL}</a></p></div></section>'''
def related_html(rel):
    if not rel: return ''
    cards=[]
    for it in rel.get('items',[]):
        s=rel_slug(it)
        if not s: continue
        cards.append(f'<a class="card" href="{U("/"+s+"/")}"><div class="card-body"><h3>{E(sub(it["title"]))}</h3><p>{E(sub(it.get("body","")))}</p><span class="card-link">Learn more</span></div></a>')
    if not cards: return ''
    return f'<section class="band band--paper"><div class="wrap"><h2>{E(rel.get("heading","You might also look at"))}</h2><div class="card-grid cols-3">{"".join(cards)}</div></div></section>'

PAGES={}
def write(path,html_):
    if 'sms:' in html_.lower(): raise SystemExit('sms link in '+path)
    if '\u2014' in html_: raise SystemExit('EM DASH in '+path+': '+html_[max(0,html_.find('\u2014')-80):html_.find('\u2014')+40])
    p=os.path.join(OUT,path.strip('/'),'index.html') if path!='/404' else os.path.join(OUT,'404.html')
    os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'w').write(html_)
def nodash(s): return s.replace(' \u2014 ',', ').replace('\u2014',', ')

LOC='Oregon, WI'
H1={'chiropractic':f'Gonstead Chiropractic in {LOC}','pediatric':f'Kids Chiropractor in {LOC}','prenatal':f'Prenatal Chiropractor in {LOC}',
 'wellness-care':f'Wellness Care in {LOC}','massage-therapy':f'Massage Therapy in {LOC}','nutrition':f'Nutrition Support in {LOC}','supplementation':f'Supplementation in {LOC}',
 'headaches':f'Headache and Migraine Chiropractor in {LOC}','whiplash':f'Whiplash and Auto Injury Chiropractor in {LOC}',
 'gonstead-system':'The Gonstead System: A 5-Part Analysis','founder-of-gonstead':'Dr. Clarence Gonstead, Founder of the Gonstead Technique',
 'first-visit':'Your First Visit','second-visit':'Your Second Visit: Report of Findings','follow-up-visit':'Follow-Up Visits'}
for _c in ['back-pain','neck-pain','sciatica','disc-injury','shoulder-pain','hip-pain','knee-pain','sports-injury','work-injury','scoliosis','arthritis']:
    H1[_c]=NAV_NAMES[_c]+f' Chiropractor in {LOC}'
def catalog_page(kind,slug,d):
    city=f"{B['city']}, {B['state']}"
    hero=d['hero']
    h1=H1[slug]
    h1=re.sub(r'\s+',' ',h1)
    sch=d.get('schema',{})
    name=nodash(sub(sch.get('name',d['title'])))
    if kind=='conditions': name=f"{d['title'].capitalize() if d['title'].islower() else d['title']} Care in {city}"
    title_map={'chiropractic':f'Gonstead Chiropractic Care in {city}','gonstead-system':f'Gonstead Technique in {city}: The 5 Components','founder-of-gonstead':'Dr. Clarence Gonstead, Founder of the Gonstead Technique','first-visit':f'Your First Gonstead Chiropractic Visit in {city}','second-visit':f'Your Second Visit: Report of Findings in {city}','follow-up-visit':f'Gonstead Follow-Up Visits in {city}'}
    if kind=='services' and slug!='chiropractic': name=f"{NAV_NAMES[slug]} in {city}"
    if kind=='conditions': name=f"{NAV_NAMES[slug]} Chiropractor in {city}"
    name=title_map.get(slug,name)
    title=f"{name} | Kratz Family Chiropractic"
    desc=nodash(sub(sch.get('description') or hero.get('sub','')))
    if kind=='conditions': desc=f"{NAV_NAMES[slug]} care from Dr. Doug Kratz, a Gonstead chiropractor in Oregon, WI. "+desc
    elif kind=='services': desc=f"{NAV_NAMES[slug]} at Kratz Family Chiropractic in Oregon, WI. "+desc
    else: desc=desc+" Kratz Family Chiropractic, Oregon, WI."
    desc=desc[:300]
    path=f'/{slug}/'
    parent={'conditions':('Conditions','/conditions/'),'services':('Services','/services/')}.get(kind,('Gonstead','/gonstead-system/'))
    trail=[('Home','/'),parent,(NAV_NAMES[slug],path)] if not (kind=='gonstead' and slug=='gonstead-system') else [('Home','/'),('Gonstead Technique',path)]
    about_type=sch.get('about_type','MedicalCondition')
    if kind=='conditions': about={"@type":"MedicalCondition","name":sch.get('about_name',d['title'])}
    else: about={"@type":"MedicalProcedure","additionalType":"https://schema.org/"+about_type if about_type!='MedicalProcedure' else None,"name":sch.get('about_name',d['title']),"procedureType":"https://schema.org/NoninvasiveProcedure"}
    wp=webpage(path,name,desc,"MedicalWebPage",about); wp["lastReviewed"]=sch.get('last_reviewed'); wp["reviewedBy"]={"@id":DOC_ID} if False else None
    schema=graph(biz_schema(),wp,crumbs_schema(trail),faq_schema(d['faqs']) if d.get('faqs') else None)
    img=catimg(hero.get('image'))
    sub_=sub(hero.get('sub',''))
    out=head(title,desc,path,schema,img or 'images/dr-kratz-portrait.jpg')+header(path)+crumbs_html(trail)
    out+=f'''<section class="page-hero"><div class="wrap"><div class="split">
<div><p class="eyebrow">{E(sub(hero.get('eyebrow','')))}</p><h1>{E(h1)}</h1><p class="lead">{E(sub_)}</p>{offer_html() if slug=='first-visit' else ''}
<p class="btn-row"><a class="btn btn--primary" href="tel:{B['tel']}">Call {B['phone']}</a> <a class="btn btn--ghost" href="{U('/request-appointment/')}">{CTA_LABEL}</a></p></div>
<div class="hero-shot" style="margin:0">{f'<img src="{U("/assets/"+img)}" alt="{E(sub(hero.get("alt","")))}" width="1400" height="933">' if img else ''}</div>
</div></div></section>'''
    out+=f'<section class="band band--paper"><div class="wrap"><div class="prose prose--wide">{blocks(d["blocks"])}</div></div></section>'
    if d.get('benefits'):
        out+='<section class="band band--mint"><div class="wrap"><h2>What you can expect here</h2><div class="benefits">'+''.join(f'<div class="benefit"><h3>{E(sub(b["title"]))}</h3><p>{E(sub(b["text"]))}</p></div>' for b in d['benefits'])+'</div></div></section>'
    if d.get('process'):
        out+='<section class="band band--paper"><div class="wrap"><h2>How care works</h2><ol class="process">'+''.join(f'<li><h3>{E(sub(b["title"]))}</h3><p>{E(sub(b["text"]))}</p></li>' for b in d['process'])+'</ol></div></section>'
    out+=faq_html(d.get('faqs'),d.get('faq_heading','Common questions'))
    out+=related_html(d.get('related'))
    cta=d.get('cta') or {}
    out+=cta_band(cta.get('heading','Ready to come in?'),None)
    out+=footer()
    write(path,out); PAGES[path]=(title,desc)

# ---------- home ----------
HOME_FAQ=[
 {"q":"Where is Kratz Family Chiropractic located?","a":"Kratz Family Chiropractic is at 600 Pleasant Oak Dr, Suite B in Oregon, Wisconsin 53575. It is our only office. Patients come from Oregon, Stoughton, Fitchburg, Brooklyn and the south Madison area. Call (608) 291-1037 to book a visit or ask a question before you come in."},
 {"q":"What is a Gonstead chiropractor?","a":"A Gonstead chiropractor uses the full spine analysis developed by Dr. Clarence Gonstead in Mt. Horeb, Wisconsin. Before adjusting, Dr. Kratz looks at five things: visualization, instrumentation, palpation, X-ray and your symptoms. The goal is to find the specific segment that needs care and adjust it by hand, leaving the rest alone."},
 {"q":"What are the office hours?","a":"The office is open Monday from 9:00 am to 6:00 pm, Tuesday and Friday from 9:00 am to 12:00 pm, and Wednesday and Thursday from 2:00 pm to 6:00 pm. We are closed on weekends. Hours can change around holidays, so call (608) 291-1037 if you are unsure."},
 {"q":"Do I need a referral to see a chiropractor in Oregon, WI?","a":"No referral is needed to book a first visit at Kratz Family Chiropractic. You can call the office directly to schedule. We have plans available for all kinds of insurance. We will go over cost with you before care starts, so there are no surprises later."},
 {"q":"What happens at a first Gonstead visit?","a":"Your first visit starts with a conversation about your health history and what brought you in. Dr. Kratz then does a full Gonstead analysis and, in most cases, your first adjustment. You will leave knowing what was found and what happens next. Plan on about 30 minutes. The New Patient special is $87.00."},
 {"q":"Does Kratz Family Chiropractic see children and families?","a":"Yes. Kratz Family Chiropractic sees patients of all ages, from kids to grandparents. The Gonstead method adjusts by hand, and the force is matched to the person on the table, so care for a child looks very different from care for an adult. Parents are welcome to stay in the room."},
]
for f in HOME_FAQ:
    n=len(f['a'].split()); assert 40<=n<=60,(f['q'],n)
def home():
    path='/'
    title='Gonstead Chiropractor in Oregon, WI | Kratz Family Chiropractic'
    desc='Kratz Family Chiropractic is a full spine Gonstead chiropractor in Oregon, WI. Dr. Doug Kratz cares for families at 600 Pleasant Oak Dr, Suite B. Call (608) 291-1037.'
    schema=graph(biz_schema(),person_schema(),webpage(path,title,desc),faq_schema(HOME_FAQ),{"@type":"WebSite","@id":SITE+'#website',"name":B['name'],"url":SITE})
    # Featured services from Dr. Kratz (Nov 23): Chiropractic, Nutritional counseling, Supplementation, Massage Therapy.
    # Homepage services restored to the original six (Dr. Kratz: leave the section as is). Supplementation stays on /services/ and in the nav, not in this grid.
    svc_cards=''.join(f'<a class="svc-card" href="{U("/"+s+"/")}"><img src="{U("/assets/"+catimg(SVC[s]["hero"]["image"]))}" alt="{E(sub(SVC[s]["hero"].get("alt","")))}" loading="lazy" width="1400" height="933"><span>{E(NAV_NAMES[s])}</span><small>{E(sub(SVC[s].get("card_blurb","")))}</small></a>' for s in HOME_SERVICES)
    six=['back-pain','neck-pain','headaches','sciatica','disc-injury','sports-injury']
    cond_cards=''.join(f'<div class="cond-card"><img src="{U("/assets/"+catimg(CON[s]["hero"]["image"]))}" alt="{E(sub(CON[s]["hero"].get("alt","")))}" loading="lazy" width="400" height="400"><div><h3>{E(NAV_NAMES[s])}</h3><p>{E(sub(CON[s]["hero"]["sub"]))}</p><a class="btn" href="{U("/"+s+"/")}">Learn more<span class="skip"> about {E(NAV_NAMES[s].lower())}</span></a></div></div>' for s in six)
    out=head(title,desc,path,schema)+header(path)
    out+=f'''<section class="k-hero"><div class="wrap k-hero-grid">
<div>
  <p class="eyebrow">Full spine Gonstead practitioner</p>
  <h1>Chiropractor <span class="accent">in Oregon, WI</span></h1>
  <p class="lead">Specific, hands-on chiropractic care for the whole family. {B['doc_short']} finds the exact source of the problem with a full Gonstead analysis, then adjusts only what needs it.</p>
  <p class="btn-row"><a class="btn btn--primary" href="{U('/request-appointment/')}">{CTA_LABEL}</a> <a class="btn btn--ghost" href="tel:{B['tel']}">Call {B['phone']}</a></p>
  <p class="np-link"><a href="{U('/first-visit/')}">New patient experience: what to expect at your first visit</a></p>
  <div class="k-answer"><span class="lbl">In short</span><p>Kratz Family Chiropractic is a Gonstead chiropractic office at {E(B['addr_full'])}. {B['doctor']}, D.C., has been in practice for 25 years and uses the full Gonstead analysis to find where your spine needs care, then adjusts by hand. Patients of all ages come from Oregon and nearby towns.</p></div>
  <ul class="k-facts"><li>25 years in practice</li><li>Full spine Gonstead analysis</li><li>Care for all ages</li><li>Oregon, WI office</li></ul>
</div>
<div class="k-hero-photo"><img src="{U('/assets/images/dr-kratz-portrait.jpg')}" alt="Dr. Doug Kratz in his Oregon, WI office" width="1200" height="1600"><div class="tag"><strong>{B['doctor']}, D.C.</strong>Gonstead chiropractor, Kratz Family Chiropractic</div></div>
</div></section>

<section class="band band--blue"><div class="wrap center">
  <h2>The care we offer</h2>
  <p class="lead">Gonstead chiropractic is at the center of everything we do, with care for kids, expecting moms and anyone who wants to stay well.</p>
  <div class="svc-grid">{svc_cards}</div>
  <p style="margin-top:1.2rem"><a class="btn btn--white" href="{U('/services/')}">All services</a></p>
</div></section>

<section class="band band--paper"><div class="wrap split">
  <div class="welcome-photos"><div class="main"><img src="{U('/assets/images/dr-kratz-spine-model.jpg')}" alt="Dr. Kratz holding a spine model in the Oregon office" loading="lazy" width="1012" height="1600"></div>
  <div class="inset"><img src="{U('/assets/images/office-exterior.jpg')}" alt="The Kratz Family Chiropractic building on Pleasant Oak Dr in Oregon, WI" loading="lazy" width="1593" height="1600"></div></div>
  <div style="padding-top:1rem">
    <p class="eyebrow">Chiropractor in Oregon, WI</p>
    <h2>Welcome to Kratz Family Chiropractic</h2>
    {bio_html()}
    <div class="k-split-cta"><a class="btn btn--primary" href="{U('/us/')}">Meet Dr. Kratz</a><p class="sig">{B['doctor']}</p></div>
  </div>
</div></section>

<section class="band band--mist"><div class="wrap">
  <p class="eyebrow">Discover Gonstead</p>
  <h2>What makes a Gonstead chiropractor different?</h2>
  <p class="lead">A Gonstead adjustment is only as good as the analysis behind it. Before {B['doc_short']} adjusts anything, five separate checks have to agree on where the problem is.</p>
  <ol class="five">
    <li><h3>Visualization</h3><p>How you stand, move and carry your posture, from the moment you walk in.</p></li>
    <li><h3>Instrumentation</h3><p>A dual-probe instrument compares temperature on both sides of the spine to find inflammation.</p></li>
    <li><h3>Palpation</h3><p>Hands-on checks of the spine, both still and in motion.</p></li>
    <li><h3>X-ray</h3><p>Full spine films, where appropriate, to see alignment and the discs.</p></li>
    <li><h3>Symptoms</h3><p>Your history and what you feel, so care fits the whole picture.</p></li>
  </ol>
  <p style="margin-top:1.2rem"><a class="btn btn--primary" href="{U('/gonstead-system/')}">The Gonstead analysis explained</a></p>
  <div class="local-note"><img src="{U('/assets/images/clarence-gonstead.jpg')}" alt="Dr. Clarence Gonstead" loading="lazy"><div><h3>Gonstead started close to home</h3><p>Dr. Clarence Gonstead developed his system in Mt. Horeb, Wisconsin, just west of Madison. Kratz Family Chiropractic carries that method forward in Oregon.</p></div><a class="btn btn--white" href="{U('/founder-of-gonstead/')}">Meet Dr. Gonstead</a></div>
</div></section>

<section class="band band--paper"><div class="wrap"><div class="npx">
  <p class="eyebrow">A new patient experience</p>
  <h2>Three visits to a clear plan</h2>
  <p>You will know what is going on, and what we recommend, before you commit to anything.</p>
  <div class="steps">
    <a class="step" href="{U('/first-visit/')}"><b>1. First visit</b><span>About 30 minutes: your history and a full Gonstead analysis.</span></a>
    <a class="step" href="{U('/second-visit/')}"><b>2. Second visit</b><span>Your report of findings, in plain language, and a recommended plan.</span></a>
    <a class="step" href="{U('/follow-up-visit/')}"><b>3. Follow-up visits</b><span>Short, specific visits that re-check and adjust what needs it.</span></a>
  </div>
  {offer_html(' np-offer--dark')}
  <p class="btn-row" style="justify-content:center"><a class="btn btn--white" href="{U('/request-appointment/')}">{CTA_LABEL}</a> <a class="btn btn--ghost" href="tel:{B['tel']}">Call {B['phone']}</a></p>
</div></div></section>

<section class="band band--mint"><div class="wrap center">
  <h2>What patients say about Kratz Family Chiropractic</h2>
  <div class="tgrid">
    {tcards()}
  </div>
  <p style="margin-top:1.2rem"><a class="btn btn--primary" href="{U('/testimonials/')}">More from our patients</a></p>
</div></section>

<section class="band band--blue"><div class="wrap">
  <h2>Chiropractic care may help these common concerns</h2>
  <p class="lead">Most people come in because something hurts. A Gonstead analysis looks for where it starts, not just where you feel it.</p>
  <div class="cond-grid">{cond_cards}</div>
  <p style="margin-top:1.4rem;text-align:center"><a class="btn btn--white" href="{U('/conditions/')}">See all conditions</a></p>
</div></section>

<section class="band band--paper"><div class="wrap">
  <p class="eyebrow">Good to know</p>
  <h2>Common questions about chiropractic care in Oregon, WI</h2>
  <div class="faq prose prose--wide">{''.join(f'<details><summary>{E(f["q"])}</summary><p>{E(f["a"])}</p></details>' for f in HOME_FAQ)}</div>
  <p><a href="{U('/faqs/')}">More questions and answers</a></p>
</div></section>

<section class="band band--mist"><div class="wrap visit">
  <div><p class="eyebrow">Visit us</p><h2>Our Oregon office</h2>
  <address class="nap"><strong>Kratz Family Chiropractic</strong><br>{E(B['street'])}<br>{B['city']}, {B['state']} {B['zip']}<br><a href="tel:{B['tel']}">{B['phone']}</a></address>
  {hours_list()}
  <p class="btn-row" style="margin-top:1rem"><a class="btn btn--primary" href="{MAPS}" target="_blank" rel="noopener">Get directions</a> <a class="btn btn--ghost" href="tel:{B['tel']}">Call the office</a></p></div>
  <iframe class="map" src="{EMBED}" title="Map to Kratz Family Chiropractic in Oregon, WI" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
</div></section>
'''
    out+=cta_band('Ready to find out what is going on?')+footer()
    write(path,out); PAGES[path]=(title,desc)

def simple(path,title,desc,h1,eyebrow,body,trail,schema_extra=(),lead=''):
    schema=graph(biz_schema(),webpage(path,title.split(' | ')[0],desc),crumbs_schema(trail),*schema_extra)
    out=head(title,desc,path,schema)+header(path)+crumbs_html(trail)
    out+=f'<section class="page-hero"><div class="wrap"><p class="eyebrow">{E(eyebrow)}</p><h1>{E(h1)}</h1>{f"<p class=lead>{E(lead)}</p>" if lead else ""}</div></section>'+body
    out+=footer(); write(path,out); PAGES[path]=(title,desc)

def about():
    body=f'''<section class="band band--paper"><div class="wrap split">
<div class="portrait"><img src="{U('/assets/images/dr-kratz-portrait.jpg')}" alt="Dr. Doug Kratz, chiropractor in Oregon, WI" width="1200" height="1600"></div>
<div class="bio"><p class="eyebrow">Doctor of Chiropractic</p><h2>{B['doctor_full']}</h2>
{bio_html()}
<p class="btn-row"><a class="btn btn--primary" href="{U('/request-appointment/')}">{CTA_LABEL}</a> <a class="btn btn--ghost" href="tel:{B['tel']}">Call {B['phone']}</a></p><p class="np-link"><a href="{U('/first-visit/')}">What to expect at your first visit</a></p></div>
</div></section>
<section class="band band--mist"><div class="wrap"><h2>Inside our Oregon office</h2>
<div class="gallery">
<figure><img src="{U('/assets/images/office-exterior.jpg')}" alt="Kratz Family Chiropractic building exterior on Pleasant Oak Dr" loading="lazy"><figcaption>600 Pleasant Oak Dr, Suite B</figcaption></figure>
<figure><img src="{U('/assets/images/office-waiting-room.jpg')}" alt="Waiting room with chairs and windows" loading="lazy"><figcaption>Waiting room</figcaption></figure>
<figure><img src="{U('/assets/images/office-front-desk.jpg')}" alt="Front desk and hallway" loading="lazy"><figcaption>Front desk</figcaption></figure>
<figure><img src="{U('/assets/images/office-adjusting-room.jpg')}" alt="Adjusting room with Gonstead tables" loading="lazy"><figcaption>Adjusting room</figcaption></figure>
<figure><img src="{U('/assets/images/dr-kratz-front-desk.jpg')}" alt="Dr. Kratz at the front desk" loading="lazy"><figcaption>{B['doc_short']} at the front desk</figcaption></figure>
<figure><img src="{U('/assets/images/dr-kratz-spine-model.jpg')}" alt="Dr. Kratz explaining the spine with a model" loading="lazy"><figcaption>Explaining the spine</figcaption></figure>
</div></div></section>'''+cta_band('Come meet Dr. Kratz')
    simple('/us/','Meet Dr. Doug Kratz, Gonstead Chiropractor in Oregon, WI | Kratz Family Chiropractic','Meet Dr. Doug Kratz, D.C., the full spine Gonstead chiropractor at Kratz Family Chiropractic in Oregon, WI, and take a look inside the office.','Meet Dr. Doug Kratz','Who we are',body,[('Home','/'),('Meet Dr. Kratz','/us/')],(person_schema(),))

def testimonials():
    body=f'<section class="band band--paper"><div class="wrap"><div class="tgrid">{tcards()}</div></div></section>'+cta_band()
    simple('/testimonials/','Patient Testimonials | Kratz Family Chiropractic, Oregon, WI','What patients say about Kratz Family Chiropractic, a Gonstead chiropractor in Oregon, WI.','Patient Testimonials','Who we are',body,[('Home','/'),('Testimonials','/testimonials/')])

def index_page(kind):
    if kind=='services':
        L=SERVICES; D=SVC; h1='Chiropractic Services in Oregon, WI'; path='/services/'
        title='Chiropractic Services in Oregon, WI | Kratz Family Chiropractic'
        desc='Gonstead chiropractic, care for kids and expecting moms, wellness care, massage therapy and nutrition support at Kratz Family Chiropractic in Oregon, WI.'
        lead='Everything here starts with a full Gonstead analysis, so each service fits what your body actually needs.'
    else:
        L=CONDITIONS; D=CON; h1='Conditions We Help With in Oregon, WI'; path='/conditions/'
        title='Conditions We Help With in Oregon, WI | Kratz Family Chiropractic'
        desc='Back pain, neck pain, headaches, sciatica, disc injuries and more. See how Gonstead chiropractic care at Kratz Family Chiropractic in Oregon, WI may help.'
        lead='Find the problem that sounds like yours. Each page explains what tends to cause it and how chiropractic care may help.'
    cards=''.join(f'<a class="card" href="{U("/"+s+"/")}"><img src="{U("/assets/"+catimg(D[s]["hero"]["image"]))}" alt="{E(sub(D[s]["hero"].get("alt","")))}" loading="lazy" width="1400" height="933"><div class="card-body"><h3>{E(NAV_NAMES[s])}</h3><p>{E(sub(D[s].get("card_blurb") or D[s]["hero"]["sub"]))}</p><span class="card-link">Learn more</span></div></a>' for s in L)
    il={"@type":"ItemList","itemListElement":[{"@type":"ListItem","position":i+1,"name":NAV_NAMES[s],"url":ORIGIN+U('/'+s+'/')} for i,s in enumerate(L)]}
    body=f'<section class="band band--paper"><div class="wrap"><div class="card-grid cols-3">{cards}</div></div></section>'+cta_band('Not sure where you fit?','Call and describe what is going on. If chiropractic is not the right fit, we will tell you.')
    simple(path,title,desc,h1,'What we do',body,[('Home','/'),(kind.capitalize(),path)],(il,),lead)

def faqs():
    d=FAQG
    allq=d['faqs']
    c=d['citation']
    dirlinks=''.join(f'<li><a href="{U("/"+s+"/")}">{E(NAV_NAMES[s])} questions</a></li>' for s in CONDITIONS+SERVICES+['first-visit','gonstead-system'])
    body=f'''<section class="band band--paper"><div class="wrap"><div class="prose prose--wide">
<div class="answer"><span class="lbl">The short answer</span><p>{E(sub(d['intro']))}</p></div>
<h2>{E(d['faq_heading'])}</h2><div class="faq">{''.join(f'<details><summary>{E(sub(f["q"]))}</summary><p>{E(sub(f["a"]))}</p></details>' for f in allq)}</div>
<div class="citation"><strong>{E(c['stat'])}</strong>{E(c['text'])} <span>{E(c['source'])}<a href="{c['link_url']}" target="_blank" rel="noopener">{E(c['link_text'])}</a></span></div>
<h2>{E(d['directory_heading'])}</h2><p>{E(d['directory_intro'])}</p><ul style="columns:2">{dirlinks}</ul>
</div></div></section>'''+cta_band(d['cta']['heading'],'Ask us directly. Call the office and get a straight answer either way.')
    simple('/faqs/','Chiropractic FAQ, Oregon, WI | Kratz Family Chiropractic','Straight answers to the questions people ask before a first chiropractic visit in Oregon, WI: safety, whether adjustments hurt, how many visits, referrals and insurance.','Questions We Hear Before Anyone Books','Good questions',body,[('Home','/'),('FAQ','/faqs/')],(faq_schema(allq),))

def contact():
    body=f'''<section class="band band--paper"><div class="wrap split" style="align-items:start">
<div><h2>Office</h2><address class="nap"><strong>Kratz Family Chiropractic</strong><br>{E(B['street'])}<br>{B['city']}, {B['state']} {B['zip']}<br><a href="tel:{B['tel']}">{B['phone']}</a></address>
<h3>Hours</h3>{hours_list()}
<p class="btn-row" style="margin-top:1rem"><a class="btn btn--primary" href="{MAPS}" target="_blank" rel="noopener">Get directions</a></p>
<iframe class="map" src="{EMBED}" title="Map to Kratz Family Chiropractic" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
<p style="margin-top:.8rem"><img src="{U('/assets/images/office-exterior.jpg')}" alt="The building at 600 Pleasant Oak Dr in Oregon, WI" loading="lazy" style="border-radius:14px;max-height:320px;width:100%;object-fit:cover"></p></div>
<div><div class="request-callout"><h2>New patient?</h2><p>Use the short appointment request form and the office will contact you after you submit to set up your first visit. Your first visit takes about {FIRST_MIN}, and the New Patient special is {NP_SPECIAL}. {INS}</p><a class="btn btn--primary" href="{U('/request-appointment/')}">{CTA_LABEL}</a></div>
<h2>Send us a message</h2>
<p>Send a short note and the office will contact you after you submit. There is no online scheduling, and our phone line is for calls only.</p>
<!-- Lead form config (inactive on preview): submissions go by email to doug@kratzfamilychiro.com (staff emails can be added later). See _build/form-config.json -->
<form class="js-contact" action="#" method="post" data-preview-inactive="true" data-form="contact">
<div><label for="f-name">Name</label><input id="f-name" name="name" autocomplete="name" required></div>
<div><label for="f-phone">Phone</label><input id="f-phone" name="phone" type="tel" autocomplete="tel"></div>
<div><label for="f-email">Email</label><input id="f-email" name="email" type="email" autocomplete="email" required></div>
<div><label for="f-msg">Message</label><textarea id="f-msg" name="message"></textarea></div>
<p class="form-note">Please do not include medical details here.</p>
<button class="btn btn--primary" type="submit">Send message</button><p class="form-status" role="status"></p>
</form></div></div></section>'''
    simple('/contact-us/','Contact Kratz Family Chiropractic, Oregon, WI','Call (608) 291-1037 or visit Kratz Family Chiropractic at 600 Pleasant Oak Dr, Suite B, Oregon, WI 53575. Address, hours, directions and a contact form.','Contact Kratz Family Chiropractic','Contact us',body,[('Home','/'),('Contact Us','/contact-us/')])

def request_appt():
    body=f'''<section class="band band--paper"><div class="wrap split" style="align-items:start">
<div id="request"><h2>Claim the $87 New Patient Special</h2>
<p>Fill out this short form and the office will contact you after you submit to find a time that works. There is no online scheduling; this sends a request and does not book a time on its own.</p>
{offer_html()}
<!-- Lead form config (inactive on preview): submissions go by email to doug@kratzfamilychiro.com (staff emails can be added later). See _build/form-config.json -->
<form class="js-contact" action="#" method="post" data-preview-inactive="true" data-form="request-appointment">
<div><label for="r-name">Name</label><input id="r-name" name="name" autocomplete="name" required></div>
<div><label for="r-phone">Phone</label><input id="r-phone" name="phone" type="tel" autocomplete="tel" required></div>
<div><label for="r-email">Email</label><input id="r-email" name="email" type="email" autocomplete="email"></div>
<div><label for="r-reason">Reason for visit</label><textarea id="r-reason" name="reason" placeholder="A few words is plenty, for example low back pain or a wellness check."></textarea></div>
<p class="form-note">Please keep medical details brief. Dr. Kratz will go over your history in person.</p>
<button class="btn btn--primary" type="submit">Send appointment request</button><p class="form-status" role="status"></p>
</form></div>
<div><div class="portrait" style="margin-bottom:1rem"><img src="{U('/assets/images/dr-kratz-front-desk.jpg')}" alt="Dr. Kratz at the front desk of the Oregon office" width="1170" height="1345"></div>
<h3>Prefer to call?</h3><p><a class="btn btn--ghost" href="tel:{B['tel']}">Call {B['phone']}</a></p>
<h3>Office hours</h3>{hours_list()}
<p style="margin-top:1rem"><a href="{U('/first-visit/')}">What to expect at your first visit</a></p></div>
</div></section>'''
    simple('/request-appointment/','Claim the $87 New Patient Special | Kratz Family Chiropractic, Oregon, WI','Claim the $87 New Patient special at Kratz Family Chiropractic in Oregon, WI. Send a short request and the office will contact you.','Claim the $87 New Patient Special','New patients',body,[('Home','/'),('Claim the $87 New Patient Special','/request-appointment/')])

def legal():
    LEGAL=json.load(open(os.path.join(HERE,'legal-src.json')))['pages']
    pages=[('privacy-policy','Privacy Policy'),('terms-of-service','Terms of Service'),('healthcare-disclaimer','Healthcare Disclaimer'),('good-faith-estimate','Good Faith Estimate'),('hipaa-privacy-practices','HIPAA Notice of Privacy Practices'),('accessibility-statement','Accessibility Statement'),('anti-discrimination','Anti-Discrimination Notice')]
    for slug,name in pages:
        prose=LEGAL[slug]
        for a,b in [('Ortloff Family Chiropractic',B['name']),('https://ortlofffamilychiropractic.com','https://kratzfamilychiro.com'),('Luke@ortlofffamilychiropractic.com',B['lead_email']),
                    ('35544 Sand Pointe Dr. Suite C',B['street']),('Crosslake, MN 56442',f"Oregon, WI 53575"),('(218) 866-5436',B['phone']),('+12188665436',B['tel']),('State of MN','State of Wisconsin')]:
            prose=prose.replace(a,b)
        bad=re.findall(r'Ortloff|Luke|Crosslake|Minnesota|\bMN\b|218',prose)
        if bad: raise SystemExit(f'leftover in {slug}: {bad}')
        title=f'{name} | Kratz Family Chiropractic'
        body=f'<section class="band band--paper"><div class="wrap">{prose}</div></div></section>'
        simple(f'/{slug}/',title,f'{name} for Kratz Family Chiropractic in Oregon, WI.',name,'Legal',body,[('Home','/'),(name,f'/{slug}/')])

def notfound():
    out=head('Page not found | Kratz Family Chiropractic','Page not found.','/404',graph(biz_schema()))+header('/404')
    out+=f'<section class="page-hero"><div class="wrap"><h1>We could not find that page</h1><p class="lead">Try the <a href="{U("/")}">home page</a> or call <a href="tel:{B["tel"]}">{B["phone"]}</a>.</p></div></section>'+footer()
    write('/404',out)

def extras():
    open(os.path.join(OUT,'robots.txt'),'w').write('User-agent: *\nDisallow: /\n')
    open(os.path.join(OUT,'.nojekyll'),'w').write('')
    urls=sorted(PAGES)
    sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{ORIGIN+U(p)}</loc></url>\n' for p in urls)+'</urlset>\n'
    open(os.path.join(OUT,'sitemap.xml'),'w').write(sm)
    hrs='; '.join(f"{d[0]} {hours_txt(d)}" for d in HOURS)
    L=[f"# {B['name']}","",f"> Full spine Gonstead chiropractor in Oregon, Wisconsin. {B['doctor']}, D.C. (Dr. Douglas Kratz). Design preview, not the live site.","",
       "## Practice facts",f"- Address: {B['addr_full']}",f"- Phone: {B['phone']}",f"- Hours: {hrs}","- Years in practice: 25",f"- Claim $87 New Patient Special: {ORIGIN+U('/request-appointment/')}","- Technique: Gonstead (full spine analysis, including visualization, instrumentation, palpation, X-ray and symptoms)",f"- First visit: about {FIRST_MIN}. New Patient special: {NP_SPECIAL}",f"- Insurance: {INS}","- Appointments: call (call only, no texting) or send the short request form; no online scheduling","- Areas served: Oregon, Stoughton, Fitchburg, Brooklyn and the south Madison area",f"- Facebook: {B['facebook']}","",
       "## Key pages"]
    for p in ['/','/us/','/gonstead-system/','/founder-of-gonstead/','/first-visit/','/second-visit/','/follow-up-visit/','/services/','/conditions/','/faqs/','/request-appointment/','/contact-us/']:
        L.append(f"- [{PAGES[p][0]}]({ORIGIN+U(p)}): {PAGES[p][1]}")
    L+=["","## Services"]+[f"- [{NAV_NAMES[s]}]({ORIGIN+U('/'+s+'/')})" for s in SERVICES]
    L+=["","## Conditions"]+[f"- [{NAV_NAMES[s]}]({ORIGIN+U('/'+s+'/')})" for s in CONDITIONS]
    open(os.path.join(OUT,'llms.txt'),'w').write('\n'.join(L)+'\n')
    open(os.path.join(OUT,'README.md'),'w').write(f"""# Kratz Family Chiropractic (design preview)

This repository is a **design preview only**. It is not the live Kratz Family Chiropractic website.

- Practice: Kratz Family Chiropractic (Dr. Doug Kratz), Oregon, Wisconsin
- Preview URL: {SITE}
- Every page is `noindex,nofollow`. `robots.txt` disallows all crawlers. Forms are inactive.
- Rebuild: `python3 _build/build.py` with the localember catalog at `LE_CATALOG`.
""")

if __name__=='__main__':
    home(); about(); testimonials(); index_page('services'); index_page('conditions'); faqs(); contact(); request_appt()
    for s,d in SVC.items(): catalog_page('services',s,d)
    for s,d in CON.items(): catalog_page('conditions',s,d)
    for s,d in GON.items(): catalog_page('gonstead',s,d)
    legal(); notfound(); extras()
    # titles unique
    ts=[v[0] for v in PAGES.values()]; dup={t for t in ts if ts.count(t)>1}
    ds=[v[1] for v in PAGES.values()]; dd={t for t in ds if ds.count(t)>1}
    if dup or dd: raise SystemExit(f'dup titles {dup} descs {dd}')
    print(len(PAGES),'pages')
