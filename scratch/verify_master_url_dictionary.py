import requests
import concurrent.futures

COMPANY_SOURCES = {
    "Nobilia": {
        "official_portal": "https://www.nobiliaindia.in/",
        "catalogue": "https://catalogue.nobilia.de/kitchen",
        "brochure_service": "https://www.nobilia.de/en/services/catalogues-and-brochures/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=nobilia",
        "indiamart_cat": "https://dir.indiamart.com/impcat/german-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/presentation/89557852/Modular-Kitchen"
    },
    "Hacker": {
        "official_portal": "https://haecker-india.com/",
        "global_portal": "https://www.haecker-kuechen.com/en/",
        "catalogue": "https://haecker-india.com/download",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=hacker",
        "indiamart_cat": "https://dir.indiamart.com/impcat/german-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/doc/264814376/Sample-Quotation"
    },
    "Veneta_Cucine": {
        "official_portal": "https://venetacucineindia.com/",
        "global_portal": "https://www.venetacucine.com/en/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=veneta+cucine",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://it.scribd.com/document/703034921/Veneta-cucine-Nuovo-Catalogo-Spazio-Aumentato-It-En"
    },
    "Nolte": {
        "official_portal": "https://nolteindia.com/",
        "global_portal": "https://www.nolte-kuechen.com/en-gb",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=nolte+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/german-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/820407790/NOLTE-Meine-Kueche-2024-Web-En"
    },
    "Scavolini": {
        "official_portal": "https://www.scavolini.com/ww/",
        "collections": "https://www.scavolini.com/ww/kitchens",
        "catalogue": "https://www.scavolini.com/ww/request-catalogue",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=scavolini",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://de.scribd.com/document/615122478/Diesel-Social-Kitchen-2022"
    },
    "SieMatic": {
        "official_portal": "https://www.siematic.com/en/",
        "collections": "https://www.siematic.com/en/kitchens/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=siematic",
        "indiamart_cat": "https://dir.indiamart.com/impcat/german-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/76872190/SieMatic-Interior-Design-for-the-Kitchen"
    },
    "Poggenpohl": {
        "official_portal": "https://www.poggenpohl.com/",
        "collections": "https://www.poggenpohl.com/kitchen-architecture/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=poggenpohl",
        "indiamart_cat": "https://dir.indiamart.com/impcat/german-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/915422435/Poggenpohl-Kitchen-Architecture"
    },
    "Boffi": {
        "official_portal": "https://www.boffi.com/en/",
        "collections": "https://www.boffi.com/en/collections/kitchens/",
        "downloads": "https://www.boffi.com/en/download/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=boffi",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/1036202576/Boffi-Kitchenology-2022"
    },
    "Poliform": {
        "official_portal": "https://www.poliform.it/en/",
        "collections": "https://www.poliform.it/en/kitchens/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=poliform",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/746438067/CA-519329249"
    },
    "Snaidero": {
        "official_portal": "https://www.snaidero.com/en/",
        "collections": "https://www.snaidero.com/en/products/icone/",
        "downloads": "https://www.snaidero.com/en/professionals/download/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=snaidero",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://id.scribd.com/document/663275531/Snaidero-Kichen"
    },
    "Pedini": {
        "official_portal": "https://www.pedini.it/en/cucine/",
        "downloads": "https://www.pedini.it/download/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=pedini",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/725399776/COCINA"
    },
    "Lineadecor": {
        "official_portal": "https://lineadecor.com/en/",
        "collections": "https://lineadecor.com/en/kitchen-models",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=lineadecor+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/italian-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/doc/264814376/Sample-Quotation"
    },
    "Wurfel": {
        "official_portal": "https://wurfel.in/",
        "collections": "https://www.wurfel.in/Luxury-Modular-kitchens.php",
        "about": "https://www.wurfel.in/about-us-Best-Modular-kitchen.php",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=wurfel+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/acrylic-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/532336105/Wurfel-Kuche-Catalogue-2019"
    },
    "Arttdinox": {
        "official_portal": "https://arttdinox.com/",
        "kitchens": "https://arttdinox.com/pages/modular-kitchens",
        "jindal_corp": "https://www.jindalstainless.com/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=arttdinox",
        "indiamart_cat": "https://dir.indiamart.com/impcat/stainless-steel-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/612091173/Jindal-Kitchen-compressed-fc032c98fd"
    },
    "Sleek_AsianPaints": {
        "official_portal": "https://www.sleekworld.com/",
        "asian_paints_portal": "https://www.beautifulhomes.asianpaints.com/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=sleek+modular+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/wooden-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/988693343/Sleek-USP-Catalogue-2025"
    },
    "HomeLane": {
        "official_portal": "https://www.homelane.com/",
        "calculator": "https://www.homelane.com/cost-calculator",
        "designs": "https://www.homelane.com/modular-kitchen-designs",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=homelane",
        "indiamart_cat": "https://dir.indiamart.com/impcat/wooden-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/810657717/INSPIRATION-BOARD-EXCUTED-PROJECTS-OF-HL-2-1-1"
    },
    "Livspace": {
        "official_portal": "https://www.livspace.com/in",
        "calculator": "https://www.livspace.com/in/interiors/kitchen-price-calculator",
        "offerings": "https://www.livspace.com/in/interiors/offerings/know-your-kitchen",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=livspace",
        "indiamart_cat": "https://dir.indiamart.com/impcat/wooden-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/722733859/Process-Livspace"
    },
    "IFB": {
        "appliances": "https://www.ifbappliances.com/",
        "modular_kitchens": "https://modularkitchen.ifbappliances.com/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=ifb+modular+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/acrylic-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/doc/264814376/Sample-Quotation"
    },
    "Design_Cafe": {
        "official_portal": "https://www.designcafe.com/",
        "calculator": "https://www.designcafe.com/modular-kitchen-cost-calculator/",
        "home_calc": "https://www.designcafe.com/home-interior-cost-calculator/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=design+cafe+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/wooden-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/796654202/Sai-Srikar-DesignCafe-Quote"
    },
    "Godrej_Interio": {
        "official_portal": "https://www.godrejinterio.com/",
        "kitchens": "https://www.godrejinterio.com/modular-kitchens",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=godrej+interio+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/stainless-steel-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/579013907/godrej-modular-kitchen-price-list-446"
    },
    "Spacewood": {
        "official_portal": "https://spacewood.in/",
        "kitchens": "https://spacewood.in/modular-kitchen-designs/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=spacewood+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/spacewood-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/document/631054891/SPACEWOOD-DESIGN-PROPOSALS"
    },
    "Hafele": {
        "official_portal": "https://home.hafeleindia.com/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=hafele+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/german-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/presentation/89557852/Modular-Kitchen"
    },
    "Panasonic": {
        "official_portal": "https://lsin.panasonic.com/",
        "kitchens": "https://lsin.panasonic.com/home-advancement-modular-kitchens-support",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=panasonic+modular+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/u-shaped-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Delhi/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/doc/264814376/Sample-Quotation"
    },
    "Casantro": {
        "official_portal": "https://casantro.com/",
        "about": "https://casantro.com/about-us/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=casantro+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/acrylic-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Mumbai/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/presentation/89557852/Modular-Kitchen"
    },
    "Itallica": {
        "tradeindia": "https://www.tradeindia.com/Seller-4131580-ITALICA-MODULAR-FURNITURE/",
        "indiamart": "https://dir.indiamart.com/search.mp?ss=italica+modular+kitchen",
        "indiamart_cat": "https://dir.indiamart.com/impcat/wooden-modular-kitchen.html",
        "justdial": "https://www.justdial.com/Bangalore/Modular-Kitchen-Dealers/nct-10368149",
        "scribd": "https://www.scribd.com/doc/264814376/Sample-Quotation"
    }
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

all_urls = set()
for c, urls in COMPANY_SOURCES.items():
    for k, u in urls.items():
        all_urls.add(u)

print(f"Parallel auditing {len(all_urls)} unique URLs with 20 workers...")

def check(u):
    try:
        r = requests.get(u, headers=headers, timeout=6, stream=True)
        return u, r.status_code
    except Exception as e:
        return u, f"ERR_{type(e).__name__}"

bad = []
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = {executor.submit(check, u): u for u in all_urls}
    for f in concurrent.futures.as_completed(futures):
        u, status = f.result()
        if str(status).startswith("ERR") or (isinstance(status, int) and status >= 400):
            print(f"FAILED: [{status}] {u}")
            bad.append((u, status))
        else:
            print(f"OK [{status}]: {u}")

print(f"\n==========================================")
print(f"TOTAL CHECKED: {len(all_urls)}")
print(f"TOTAL FAILED:  {len(bad)}")
print(f"==========================================")
for b in bad:
    print(b)
