import requests
from concurrent.futures import ThreadPoolExecutor

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

candidates = [
    # Nobilia
    ('Nobilia Portal', 'https://www.nobilia.de/en/'),
    ('Nobilia India', 'https://www.nobiliaindia.in/'),
    ('Nobilia Brochures', 'https://www.nobilia.de/en/services/catalogues-and-brochures/'),
    ('Nobilia Kitchens', 'https://www.nobilia.de/en/products/kitchens/'),
    # Haecker
    ('Haecker India', 'https://haecker-india.com/'),
    ('Haecker Kitchens Global', 'https://www.haecker-kuechen.com/en/'),
    ('Haecker German Products', 'https://www.haecker-kuechen.com/en/kitchens/'),
    # Hafele
    ('Hafele India', 'https://www.hafeleindia.com/en/'),
    ('Hafele Appliances', 'https://hafeleappliances.com/'),
    ('Hafele Global', 'https://www.hafele.com/en/'),
    # Wurfel
    ('Wurfel India', 'https://wurfel.in/'),
    ('Wurfel Kitchens', 'https://wurfel.in/modular-kitchen-designs/'),
    ('Wurfel Wardrobes', 'https://wurfel.in/wardrobe-designs/'),
    # Sleek / Asian Paints
    ('Sleek World', 'https://www.sleekworld.com/'),
    ('Asian Paints Kitchens', 'https://www.asianpaints.com/more/modular-kitchens.html'),
    ('Beautiful Homes', 'https://www.beautifulhomes.asianpaints.com/'),
    # HomeLane
    ('HomeLane Main', 'https://www.homelane.com/'),
    ('HomeLane Kitchens', 'https://www.homelane.com/modular-kitchen-designs'),
    ('HomeLane Cost Calculator', 'https://www.homelane.com/cost-calculator'),
    # Livspace
    ('Livspace Main', 'https://www.livspace.com/in'),
    ('Livspace Kitchens', 'https://www.livspace.com/in/modular-kitchen-designs'),
    ('Livspace Price Calculator', 'https://www.livspace.com/in/price-calculator'),
    # Godrej Interio
    ('Godrej Interio Main', 'https://www.godrejinterio.com/'),
    ('Godrej Kitchens', 'https://www.godrejinterio.com/modular-kitchens'),
    # IFB
    ('IFB Home', 'https://www.ifbappliances.com/'),
    ('IFB Kitchens', 'https://www.ifbappliances.com/living/kitchen'),
    # Panasonic
    ('Panasonic Life Solutions', 'https://lsin.panasonic.com/'),
    ('Panasonic Housing', 'https://housing.panasonic.com/'),
    # Spacewood
    ('Spacewood Main', 'https://spacewood.in/'),
    ('Spacewood Modular Kitchen', 'https://spacewood.in/modular-kitchen/'),
    ('Spacewood Kitchen', 'https://spacewood.in/kitchen/'),
    # Arttdinox
    ('Arttdinox Main', 'https://arttdinox.com/'),
    ('Arttdinox Kitchens', 'https://arttdinox.com/pages/modular-kitchens'),
    # Casantro
    ('Casantro Main', 'https://casantro.com/'),
    ('Casantro About', 'https://casantro.com/about-us/'),
    # Design Cafe
    ('Design Cafe Main', 'https://www.designcafe.com/'),
    ('Design Cafe Kitchens', 'https://www.designcafe.com/modular-kitchen-designs/'),
    # Poliform
    ('Poliform Main', 'https://www.poliform.it/en/'),
    ('Poliform Kitchens', 'https://www.poliform.it/en/kitchens/'),
    # Boffi
    ('Boffi Main', 'https://www.boffi.com/en/'),
    ('Boffi Kitchens', 'https://www.boffi.com/en/collections/kitchens/'),
    # Poggenpohl
    ('Poggenpohl Main', 'https://www.poggenpohl.com/'),
    ('Poggenpohl Kitchens', 'https://www.poggenpohl.com/kitchens/'),
    # SieMatic
    ('SieMatic Main', 'https://www.siematic.com/en/'),
    ('SieMatic Kitchens', 'https://www.siematic.com/en/kitchens/'),
    # Veneta Cucine
    ('Veneta Cucine Global', 'https://www.venetacucine.com/en/'),
    ('Veneta Cucine India', 'https://venetacucineindia.com/'),
    # Nolte
    ('Nolte Kitchens Global', 'https://www.nolte-kuechen.com/en/'),
    ('Nolte India', 'https://nolteindia.com/'),
    # Scavolini
    ('Scavolini Global', 'https://www.scavolini.com/'),
    ('Scavolini Kitchens', 'https://www.scavolini.com/en/kitchens/'),
    # Snaidero
    ('Snaidero Global', 'https://www.snaidero.com/en/'),
    ('Snaidero Kitchens', 'https://www.snaidero.com/en/kitchens/'),
    # Pedini
    ('Pedini Global', 'https://www.pedini.it/'),
    ('Pedini Kitchens', 'https://www.pedini.it/en/cucine/'),
    # Lineadecor
    ('Lineadecor Global', 'https://lineadecor.com/'),
    ('Lineadecor Kitchens', 'https://lineadecor.com/en/kitchens/'),
]

def check(item):
    label, url = item
    try:
        r = requests.get(url, headers=headers, timeout=5, stream=True)
        return (label, url, r.status_code, '')
    except Exception as e:
        return (label, url, 0, str(e)[:35])

with ThreadPoolExecutor(max_workers=25) as ex:
    results = list(ex.map(check, candidates))

for label, url, code, err in sorted(results, key=lambda x: (x[2], x[0])):
    status = f'[{code}]' if code > 0 else f'[ERR: {err}]'
    print(f'{status:10} {label:28} {url}')
