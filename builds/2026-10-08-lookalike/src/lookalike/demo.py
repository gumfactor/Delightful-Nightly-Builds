"""Synthetic sample data. Every business here is fictional."""
from __future__ import annotations

HEADER = "id,business_name,website,phone,email,address,city,province,postal_code,category,description\n"
ROWS = [
    # duplicate cluster 1: bakery listed three ways
    '1,Maple Hearth Bakery,https://www.maplehearth.example,416-555-0101,hello@maplehearth.example,"12 Queen St W",Toronto,ON,M5H 2N2,Bakery,Sourdough and rye baked daily',
    '2,The Maple Hearth Bakery Inc.,maplehearth.example/contact,(416) 555-0101,,"12 Queen Street West, Suite 3",Toronto,Ontario,m5h2n2,Bakery; Cafe,',
    '3,Maple Hearth Bakry,,+1 416 555 0101,,,Toronto,ON,,,Family run Canadian bakery since 1987',
    # duplicate cluster 2: French/English legal suffix variants
    '4,Boulangerie Dubé Ltée,https://boulangeriedube.example,514-555-0144,,"88 rue Saint-Denis",Montréal,QC,H2X 3K8,Bakery,',
    '5,Boulangerie Dube,https://www.boulangeriedube.example/,(514) 555-0144,info@boulangeriedube.example,"88 Saint-Denis St.",Montreal,Québec,H2X3K8,Boulangerie,Pain artisanal',
    # chain: same brand, different locations (must stay separate)
    '6,Northern Lights Outfitters,https://northernlights.example,613-555-0160,,"410 Bank St",Ottawa,ON,K2P 1Y6,Outdoor gear,',
    '7,Northern Lights Outfitters,https://northernlights.example,905-555-0170,,"2200 Dundas St E",Mississauga,ON,L4X 2V3,Outdoor gear,',
    '8,Northern Lights Outfitters,https://northernlights.example,604-555-0180,,"1500 Robson St",Vancouver,BC,V6G 1C3,Outdoor gear,',
    # ambiguous: same phone, loosely similar name, different domain
    '9,Cedar Ridge Woodworks,https://cedarridgewood.example,705-555-0190,,"7 Mill Rd",Huntsville,ON,P1H 1A1,Furniture,Handmade tables',
    '10,Cedar Ridge Cabinetry,,705-555-0190,,,Huntsville,ON,,Furniture,',
    # name collision, different places (distinct)
    '11,Sunrise Cafe,https://sunrisecafe-nb.example,506-555-0120,,"15 Water St",Saint John,NB,E2L 1A1,Cafe,',
    '12,Sunrise Cafe,https://sunrisecafe-ab.example,403-555-0121,,"900 8 Ave SW",Calgary,AB,T2P 1H3,Cafe,',
    # singletons
    '13,Tidewater Candle Co.,https://tidewatercandles.example,902-555-0133,,"3 Harbour Dr",Halifax,NS,B3J 1A1,Home goods,',
    '14,Prairie Wind Honey,https://prairiewindhoney.example,306-555-0155,,"RR 2",Saskatoon,SK,S7K 1A1,Food,',
]


def sample_csv() -> str:
    return HEADER + "\n".join(ROWS) + "\n"
