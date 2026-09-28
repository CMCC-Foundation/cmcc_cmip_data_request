#!/usr/bin/env python
"""Build the CMCC AR7-FT Data Request slides for the CMCC/NorESM meeting.

Source: dr.pptx - the extract from the colleague's deck (title, closing, and the
two slides assigned to us, each carrying his placeholder).
Output: dr_filled.pptx - THREE content slides, title and closing dropped:

  (1) opportunities considered      (new slide, duplicated from the template)
  (2) scope and variables
  (3) volumes, incl. the AR7-FT campaign total

Every template shape (header band, title, rules, logo) is kept; only the
placeholder text box is replaced. Figures come from cmcc_selection/out/.

Terminology: what the tooling calls `true_gap` is presented as "new CMIP7
variables" - requested by the Data Request but not produced by CMCC-ESM3 today.

Run:  python build_slides.py        (needs the pptx skill's add_slide/clean)
"""
import os, re, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "dr.pptx")
OUT = os.path.join(HERE, "dr_filled.pptx")
WORK = "/private/tmp/claude-501/-Users-giovanniconti-Documents-dr-cmip7/56a7b982-1a6d-4372-b98e-a64d0dc2cbc8/scratchpad/build"
SKILL = ("/Users/giovanniconti/Library/Application Support/Claude/"
         "local-agent-mode-sessions/skills-plugin/5fae7c47-aaae-4d6a-acc3-46eaa2b97d87/"
         "8f12d69a-aeef-4aed-bf6b-bd7f3aa9ef54/skills/pptx/scripts")

E = 914400                      # EMU per inch
HEAD = "Montserrat"             # template title font
BODY = "Roboto"                 # template body font
NAVY = "1F3864"
BLUE = "4472C4"
BLUE_L = "8FAADC"
ORANGE = "ED7D31"
GREY = "595959"
GREY_L = "A5A5A5"
CARD = "F1F4F9"
BLACK = "000000"

FT_YEARS = 2500                 # AR7 fast-track simulation plan (CMCC estimate)

_id = [900]
def nid():
    _id[0] += 1
    return _id[0]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run(text, sz=1350, b=0, color=BLACK, font=BODY, i=0):
    return (f'<a:r><a:rPr lang="en-GB" sz="{sz}" b="{b}" i="{i}">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:latin typeface="{font}"/><a:ea typeface="{font}"/>'
            f'<a:cs typeface="{font}"/><a:sym typeface="{font}"/></a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r>')


def para(runs, algn="l", after=0, before=0, line=100, bullet=None, bucolor=None,
         marL=0, indent=0):
    bu = '<a:buNone/>'
    if bullet:
        bu = (f'<a:buClr><a:srgbClr val="{bucolor or BLUE}"/></a:buClr>'
              f'<a:buFont typeface="Arial"/><a:buChar char="{bullet}"/>')
    return (f'<a:p><a:pPr marL="{marL}" indent="{indent}" algn="{algn}" rtl="0">'
            f'<a:lnSpc><a:spcPct val="{line*1000}"/></a:lnSpc>'
            f'<a:spcBef><a:spcPts val="{before}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{after}"/></a:spcAft>{bu}</a:pPr>'
            f'{"".join(runs)}</a:p>')


def txbox(x, y, w, h, paras, anchor="t", margin=0.0):
    m = int(margin * E)
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{nid()}" name="tb{nid()}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{int(x*E)}" y="{int(y*E)}"/>'
            f'<a:ext cx="{int(w*E)}" cy="{int(h*E)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/>'
            f'<a:ln><a:noFill/></a:ln></p:spPr><p:txBody>'
            f'<a:bodyPr spcFirstLastPara="1" wrap="square" lIns="{m}" tIns="{m}" '
            f'rIns="{m}" bIns="{m}" anchor="{anchor}" anchorCtr="0"><a:noAutofit/>'
            f'</a:bodyPr><a:lstStyle/>{"".join(paras)}</p:txBody></p:sp>')


def rect(x, y, w, h, fill, rad=None):
    geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    if rad:
        adj = int(rad * 100000 / min(w, h))
        geom = (f'<a:prstGeom prst="roundRect"><a:avLst>'
                f'<a:gd name="adj" fmla="val {adj}"/></a:avLst></a:prstGeom>')
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{nid()}" name="rc{nid()}"/><p:cNvSpPr/>'
            f'<p:nvPr/></p:nvSpPr><p:spPr><a:xfrm>'
            f'<a:off x="{int(x*E)}" y="{int(y*E)}"/>'
            f'<a:ext cx="{int(w*E)}" cy="{int(h*E)}"/></a:xfrm>{geom}'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/>'
            f'<a:p><a:pPr algn="l" rtl="0"><a:buNone/></a:pPr></a:p></p:txBody></p:sp>')


# ---------------------------------------------------------------- components
def kicker(text):
    return txbox(0.85, 1.24, 11.63, 0.34,
                 [para([run(text, sz=1250, color=GREY, i=1)])])


def stat_cards(cards):
    """cards = [(number, unit, label), ...] - three equal cards across the slide."""
    out, x, w = [], 0.85, 3.71
    for num, unit, label in cards:
        out.append(rect(x, 1.66, w, 1.20, CARD, rad=0.08))
        runs = [run(num, sz=3200, b=1, color=NAVY, font=HEAD)]
        if unit:
            runs.append(run(" " + unit, sz=1500, b=1, color=BLUE, font=HEAD))
        out.append(txbox(x + 0.06, 1.72, w - 0.12, 1.10,
                         [para(runs, after=200, line=95),
                          para([run(label, sz=1100, color=GREY)], line=105)],
                         margin=0.12))
        x += w + 0.25
    return out


def col_head(x, y, text, w=5.55):
    return txbox(x, y, w, 0.36, [para([run(text, sz=1600, b=1, color=NAVY, font=HEAD)])])


def bullets(x, y, w, h, items, sz=1300):
    ps = [para([run(t, sz=sz)], bullet="•", marL=190500, indent=-190500,
               after=500, line=104) for t in items]
    return txbox(x, y, w, h, ps)


def footnote(y, lines):
    ps = [para([run(t, sz=1000, color=GREY)], after=100, line=110) for t in lines]
    return txbox(0.85, y, 11.63, 0.85, ps)


# ------------------------------------------------------- slide (1) opportunities
# High/Medium as recorded in CMCC_CMIP7-DR-opportunities-Final - DR-Selection.csv
OPPS = [
    ("ESYDA", [
        ("Baseline Climate Variables for Earth System Modelling", "high"),
        ("Benchmarking and Attributing Changes to Global Carbon and other "
         "Biogeochemical Cycles", "high"),
        ("Changes in marine biogeochemical cycles and ecosystem processes", "high"),
        ("Constructing a Global Carbon Budget", "high"),
        ("Earth's Energy Budget", "high"),
        ("Ocean changes, drivers and impacts", "high"),
        ("Role of fire in the Earth system", "high"),
        ("Sea ice changes, drivers and impacts", "high"),
        ("Terrestrial Biodiversity", "high"),
        ("Accurate assessment of land-atmosphere coupling", "medium"),
        ("Climate impacts on marine biodiversity and ecosystems", "medium"),
        ("Ocean Extremes", "medium"),
    ]),
    ("ESYDA + ICR", [
        ("Assessments for Hydrological Processes, Water Resources, and "
         "Freshwater Systems", "high"),
        ("Land use change", "high"),
        ("Plant Phenology", "high"),
        ("Water cycle/budget assessment", "high"),
    ]),
    ("CLIVAP", [
        ("Atmospheric dynamics and variability", "high"),
        ("Detection and Attribution", "high"),
        ("Diagnosing temperature variability and extremes", "high"),
        ("Dynamical Downscaling (CORDEX)", "high"),
        ("Multi-annual-to-decadal predictability of the Earth System and risk "
         "assessment of climate extremes", "high"),
        ("Robust Risk Assessment of Tipping Points", "medium"),
    ]),
    ("ICR", [
        ("Agriculture and Food System Impacts", "high"),
        ("Vulnerability of urban systems, infrastructure and populations", "high"),
        ("Water Security and Freshwater Ecosystem Services", "high"),
        ("Bias-adjustment for impacts modeling and analysis", "medium"),
        ("Impacts of climate change on aviation", "medium"),
        ("Impacts of climate change on transport infrastructure", "medium"),
    ]),
    ("EIEE", [
        ("Energy System Impacts", "medium"),
        ("Health Impacts", "medium"),
    ]),
]
COLUMNS = [["ESYDA"], ["ESYDA + ICR", "CLIVAP"], ["ICR", "EIEE"]]


def slide_opportunities():
    s = [kicker("The 30 opportunities of the Data Request v1.2.2.4 selected by the "
                "CMCC Divisions — 21 High and 9 Medium priority, 117 variable "
                "groups in total")]
    s.append(txbox(0.85, 1.60, 11.63, 0.30,
                   [para([run("High priority in black, Medium in grey. An "
                              "opportunity is a science-driven bundle of variable "
                              "groups defined by the Data Request.",
                              sz=1000, color=GREY, i=1)])]))
    groups = {name: items for name, items in OPPS}
    x, w = 0.85, 3.71
    for col in COLUMNS:
        ps = []
        for gname in col:
            items = groups[gname]
            if ps:
                ps.append(para([run(" ", sz=700)], after=0))
            ps.append(para([run(f"{gname}  ({len(items)})", sz=1250, b=1,
                                color=NAVY, font=HEAD)], after=300))
            for title, prio in items:
                col_txt = BLACK if prio == "high" else GREY
                ps.append(para([run(title, sz=1050, color=col_txt)],
                               bullet="•", bucolor=BLUE if prio == "high" else GREY_L,
                               marL=152400, indent=-152400, after=280, line=102))
        s.append(txbox(x, 1.98, w, 3.45, ps))
        x += w + 0.25

    # what each Division's selection pulls in (shared ESYDA+ICR counted in both)
    per_div = [("ESYDA", 16, 544, 232), ("CLIVAP", 6, 270, 95),
               ("ICR", 10, 146, 53), ("EIEE", 2, 33, 14)]
    x, w = 0.85, 2.74
    for name, n_opp, n_var, n_new in per_div:
        s.append(rect(x, 5.50, w, 0.92, CARD, rad=0.08))
        s.append(txbox(x + 0.06, 5.56, w - 0.12, 0.84, [
            para([run(name, sz=1250, b=1, color=NAVY, font=HEAD)], after=180),
            para([run(f"{n_opp} opportunities · {n_var} variables",
                      sz=950, color=GREY)], after=60),
            para([run(f"{n_new} new CMIP7 variables", sz=950, color=ORANGE)]),
        ], margin=0.12))
        x += w + 0.22

    s.append(footnote(6.62, [
        "Four hydrology and land opportunities are shared between ESYDA and ICR. "
        "Every variable group of every opportunity above is expanded in full — "
        "no per-variable filtering — which is what produces the 853 requested "
        "variables on the next slide.",
    ]))
    return s


# ------------------------------------------------------- slide (2) variables
def slide_variables():
    s = [kicker("Internal CMCC selection expanded against the official CMIP7 Data "
                "Request (v1.2.2.4) and cross-checked against CMCC-ESM3 output")]
    s += stat_cards([("30", "", "opportunities selected — 21 High, 9 Medium — "
                               "across 4 CMCC Divisions"),
                     ("117", "", "variable-group references, every one expanded "
                                 "in full"),
                     ("853", "", "requested variables — 660 distinct CMOR "
                                 "names across frequencies")])

    s.append(col_head(0.85, 3.16, "Selection criteria"))
    s.append(bullets(0.85, 3.58, 5.55, 2.45, [
        "CMCC per-opportunity priority: High + Medium; every variable of every "
        "listed group, no per-variable DR priority filter",
        "Selection made on DR v1.2.2.2, expanded on v1.2.2.4 with data_request_api "
        "— 2 groups renamed in between, re-pointed by name",
        "All 117 requested groups located in the DR (115 directly, 2 renamed); the "
        "build aborts rather than drop a request",
    ]))
    s.append(txbox(0.85, 5.58, 5.55, 0.34,
                   [para([run("What comes out", sz=1300, b=1, color=NAVY, font=HEAD)])]))
    s.append(bullets(0.85, 5.92, 5.55, 0.62, [
        "Production tables: frequency | ave/inst | raw model variables",
        "Every variable traced back to Division, opportunity and group",
    ], sz=1150))

    s.append(col_head(6.93, 3.16, "Can CMCC-ESM3 produce them?"))
    # stacked bar: 436 produced / 67 derivable / 350 new CMIP7 variables of 853
    x, w, y = 6.93, 5.55, 3.62
    for n, c in ((436, BLUE), (67, BLUE_L), (350, ORANGE)):
        ww = w * n / 853.0
        s.append(rect(x, y, ww, 0.26, c))
        x += ww
    rows = [("436", BLUE, "produced today — CMOR name maps to a raw model field"),
            ("67", BLUE_L, "derivable — slice or average of a field already "
                           "stored, no extra storage"),
            ("350", ORANGE, "NEW CMIP7 variables — requested, not produced by "
                            "CMCC-ESM3 today")]
    yy = 4.06
    for num, color, label in rows:
        s.append(rect(6.93, yy + 0.07, 0.13, 0.13, color))
        s.append(txbox(7.16, yy - 0.05, 0.72, 0.34,
                       [para([run(num, sz=1450, b=1, color=NAVY, font=HEAD)])]))
        s.append(txbox(7.92, yy - 0.03, 4.56, 0.62,
                       [para([run(label, sz=1150)], line=104)]))
        yy += 0.60
    s.append(txbox(6.93, 5.72, 5.55, 0.62,
                   [para([run("New CMIP7 variables by realm: land 96, atmos 65, "
                              "ocean BGC 55, aerosol 49, ocean 34, atmos chemistry "
                              "23, sea ice 18, land ice 10. Aerosol and atmospheric "
                              "chemistry are almost entirely new (2 of 75 "
                              "producible).", sz=1100, color=GREY, i=1)], line=104)]))

    s.append(footnote(6.72, [
        "853 counts one entry per requested variable × frequency × statistic "
        "(the unit the model output configuration needs); the same field at daily and "
        "monthly is one raw model variable, hence 660 distinct CMOR names.",
    ]))
    return s


# ------------------------------------------------------- slide (3) volumes
def slide_volumes():
    prod, new = 212.71, 224.34
    pb = lambda gb_yr: gb_yr * FT_YEARS / 1024 / 1024      # GB/yr -> PB over the run
    s = [kicker("Storage cost on the CMCC-ESM3 grid — GB per simulated "
                "model-year, uncompressed on-disk size")]
    s += stat_cards([("213", "GB/yr", "produced today — about 2× a CMIP6 "
                                      "model-year"),
                     ("+224", "GB/yr", "extra storage for the new CMIP7 variables"),
                     ("437", "GB/yr", "full request ≈ 4.4× CMIP6; "
                                      "derivable variables are free")])

    # the campaign total: GB/model-year x the AR7 fast-track simulation plan
    s.append(rect(0.85, 2.98, 11.63, 0.56, CARD, rad=0.08))
    s.append(txbox(0.97, 2.98, 11.39, 0.56,
                   [para([run(f"AR7 fast-track ≈ {FT_YEARS} model-years  →  ",
                              sz=1250, b=1, color=NAVY, font=HEAD),
                          run(f"{pb(prod):.2f} PB", sz=1250, b=1, color=BLUE, font=HEAD),
                          run(" produced  ·  ", sz=1250, color=GREY),
                          run(f"+{pb(new):.2f} PB", sz=1250, b=1, color=ORANGE, font=HEAD),
                          run(" new CMIP7 variables  ·  ", sz=1250, color=GREY),
                          run(f"{pb(prod + new):.2f} PB", sz=1250, b=1, color=NAVY,
                              font=HEAD),
                          run(" full request", sz=1250, color=GREY)])], anchor="ctr"))

    s.append(col_head(0.85, 3.66, "Where the cost sits", w=6.10))
    s.append(bullets(0.85, 4.06, 6.10, 2.20, [
        "Ocean 3-hourly is the whole story: 174 of the 224 GB of new variables "
        "(daily 41, monthly 10)",
        "Two fields alone are 76 % of it — ficeberg 86 and hfrunoffds 85 GB/yr",
        "One 3-D ocean field at 3hr ≈ 92 GB/yr; a 3-D atmos field ≈ 33 GB/yr",
        "6-hourly and 1-hourly requests need nothing new — 82 and 14 GB/yr, "
        "produced today",
    ], sz=1250))
    s.append(rect(0.85, 6.02, 6.10, 0.50, CARD, rad=0.08))
    s.append(txbox(0.97, 6.02, 5.86, 0.50,
                   [para([run("Trimming lever: ", sz=1200, b=1, color=NAVY, font=HEAD),
                          run("ocean sub-daily 3-D output", sz=1200, b=1,
                              color=ORANGE, font=HEAD)])], anchor="ctr"))

    s.append(col_head(7.45, 3.66, "GB per model-year", w=5.03))
    bars = [("CMIP6 reference", [(100, GREY_L)], "100"),
            ("Produced today", [(213, BLUE)], "213"),
            ("Full request", [(213, BLUE), (224, ORANGE)], "437")]
    y = 4.10
    for label, segs, total in bars:
        s.append(txbox(7.45, y - 0.02, 5.03, 0.28,
                       [para([run(label, sz=1100, color=GREY)])]))
        x = 7.45
        for val, c in segs:
            w = 4.60 * val / 437.0
            s.append(rect(x, y + 0.26, w, 0.28, c))
            x += w
        s.append(txbox(x + 0.06, y + 0.24, 1.00, 0.32,
                       [para([run(total, sz=1250, b=1, color=NAVY, font=HEAD)])]))
        y += 0.72
    s.append(txbox(7.45, 6.28, 5.03, 0.30,
                   [para([run("blue = produced   ·   orange = new CMIP7 variables",
                              sz=1000, color=GREY, i=1)])]))

    s.append(footnote(6.66, [
        "Grid: CAM/CLM spectral element ncol 48600 × L58, NEMO 360×291 "
        "× L75, float32; calibrated on a real B1850 run and validated against "
        "its files (thetao monthly 377 MB/yr, zos 5 MB/yr). Archived, deflated size "
        "≈ half. 1 PB = 1024 TB = 1024² GB.",
        "New CMIP7 variables are tracked as open rows in the per-component "
        "CMOR↔raw lookup tables (386 to resolve): fill the raw model name and "
        "the variable enters the production list automatically.",
    ]))
    return s


TITLES = {1: "CMCC AR7-FT Data Request (1)",
          2: "CMCC AR7-FT Data Request (2)",
          3: "CMCC AR7-FT Data Request (3)"}

NOTES = {
 2: ("Starting point is our internal selection of AR7 fast-track opportunities: "
     "30 opportunities marked High or Medium by four Divisions, which expand to 117 "
     "variable-group references. We take every variable of every listed group - no "
     "per-variable filtering - and expand them against the official Data Request "
     "v1.2.2.4 with the data_request_api. Two release versions are involved: the "
     "selection was written against DR v1.2.2.2, we expand on v1.2.2.4, and two "
     "groups were renamed in between - omip_geometry_physics is now "
     "omip_scalars_high_priority, hydro_modelling_PET_daily is now "
     "WaterResourcesPET_daily - so they are re-pointed by name. Coverage is then "
     "checked group by group: of 118 parsed tokens, 115 match the DR directly, 2 "
     "are the renamed ones, 1 is a free-text fragment from the spreadsheet (the "
     "word 'not' in the Ocean Extremes cell) and is discarded, and none is left "
     "unresolved. Had one been unresolved the script exits non-zero, so the "
     "pipeline cannot silently produce a shorter list. That gives 853 requests, "
     "i.e. 660 distinct CMOR variables across frequencies. Against the CMCC-ESM3 "
     "output we then have 436 already producible, 67 derivable from fields we "
     "already store, and 350 new CMIP7 variables - requested but not produced "
     "today, concentrated in aerosol and atmospheric chemistry, land carbon and "
     "ocean biogeochemistry."),
 3: ("Volumes are per simulated model-year on the CMCC-ESM3 grid, uncompressed. We "
     "produce about 213 GB per model-year today, roughly twice a CMIP6 model-year; "
     "the full request would be 437 GB, about 4.4 times CMIP6. Derivable variables "
     "add nothing because they are slices of stored fields. Over the fast-track "
     "plan of roughly 2500 model-years that is about half a petabyte for what we "
     "produce today and just over one petabyte for the full request, halved again "
     "if the archive is deflated. The cost is extremely concentrated: 174 of the "
     "224 GB of new variables is ocean 3-hourly, and two fields - ficeberg and "
     "hfrunoffds - are 76 % of it. So the decision to take is about ocean "
     "sub-daily 3-D output, not about 350 variables. The estimate is calibrated on "
     "a real B1850 run and validated against its files. The new variables are "
     "tracked as open rows in the lookup tables that map CMOR names to raw model "
     "fields."),
}


# ------------------------------------------------------------------ packaging
def sh(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True,
                       cwd=SKILL)
    if r.returncode:
        sys.exit(f"{args}\n{r.stdout}{r.stderr}")
    return r.stdout.strip()


def slide_of_rid(work):
    rels = open(f"{work}/ppt/_rels/presentation.xml.rels").read()
    return {rid: os.path.basename(t) for rid, t in
            re.findall(r'Id="([^"]+)"[^>]*Target="slides/([^"]+)"', rels)}


def keep_slides(work, ordered):
    """Rewrite <p:sldIdLst> to exactly `ordered` (slideN.xml names), in that order."""
    p = f"{work}/ppt/presentation.xml"
    xml = open(p).read()
    of_rid = slide_of_rid(work)
    entries = re.findall(r'<p:sldId [^/]*?r:id="(rId\d+)"\s*/>', xml)
    by_slide = {of_rid[rid]: rid for rid in entries if rid in of_rid}
    missing = [s for s in ordered if s not in by_slide]
    assert not missing, f"not in sldIdLst: {missing}"
    new = "".join(f'<p:sldId id="{256 + i}" r:id="{by_slide[s]}"/>'
                  for i, s in enumerate(ordered))
    xml = re.sub(r'<p:sldIdLst>.*?</p:sldIdLst>', f'<p:sldIdLst>{new}</p:sldIdLst>',
                 xml, flags=re.S)
    open(p, "w").write(xml)


def set_title(xml, text):
    """Replace the text of the title text box (the only run in white/lt1)."""
    m = re.search(r'(<a:r><a:rPr lang="[^"]*" sz="3200" b="1">.*?<a:t>)(.*?)(</a:t>)',
                  xml, re.S)
    assert m, "title run not found"
    return xml[:m.start(2)] + esc(text) + xml[m.end(2):]


def fill(xml, body_shapes, title):
    """Drop the placeholder body text box, set the title, append composed shapes."""
    k = xml.index("spAutoFit")
    start = xml.rindex("<p:sp>", 0, k)
    end = xml.index("</p:sp>", k) + len("</p:sp>")
    assert "Summary on selected opportunities" in xml[start:end], \
        "the shape found is not the colleague's placeholder"
    xml = xml[:start] + xml[end:]
    xml = set_title(xml, title)
    return xml.replace("</p:spTree>", "".join(body_shapes) + "</p:spTree>")


def set_notes(path, text):
    xml = open(path).read()
    body = re.search(r'(<p:sp>(?:(?!</p:sp>).)*?type="body".*?</p:sp>)', xml, re.S)
    if not body:
        return False
    new_p = ('<a:p><a:pPr rtl="0"><a:buNone/></a:pPr>'
             f'<a:r><a:rPr lang="en-GB" sz="1200"/><a:t>{esc(text)}</a:t></a:r></a:p>')
    sp = body.group(1)
    sp2 = re.sub(r'(<a:lstStyle/>).*?(</p:txBody>)', r'\1' + new_p + r'\2', sp,
                 flags=re.S)
    open(path, "w").write(xml.replace(sp, sp2))
    return True


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    with zipfile.ZipFile(SRC) as z:
        z.extractall(WORK)

    # --- structure first: duplicate a content slide for the new (1), then keep
    # only the three content slides (title and closing dropped by the colleagues)
    made = sh(os.path.join(SKILL, "add_slide.py"), WORK, "slide2.xml",
              "--after", "slide3.xml")
    new_slide = os.path.basename(re.search(r'(slide\d+\.xml)', made).group(1))
    print(f"[struct] duplicated slide2.xml -> {new_slide} (no shared notes)")
    keep_slides(WORK, [new_slide, "slide2.xml", "slide3.xml"])
    sh(os.path.join(SKILL, "clean.py"), WORK)
    print("[struct] kept 3 slides, dropped title/closing + orphaned media")

    # --- then content
    for n, (slide, builder) in enumerate(
            ((new_slide, slide_opportunities),
             ("slide2.xml", slide_variables),
             ("slide3.xml", slide_volumes)), start=1):
        p = f"{WORK}/ppt/slides/{slide}"
        with open(p) as f:
            filled = fill(f.read(), builder(), TITLES[n])
        with open(p, "w") as f:
            f.write(filled)
        print(f"[fill]   {slide} -> {TITLES[n]}")

    for n, text in NOTES.items():
        slide = {2: "slide2.xml", 3: "slide3.xml"}[n]
        rels = open(f"{WORK}/ppt/slides/_rels/{slide}.rels").read()
        m = re.search(r'notesSlide(\d+)\.xml', rels)
        if m and set_notes(f"{WORK}/ppt/notesSlides/notesSlide{m.group(1)}.xml", text):
            print(f"[notes]  {slide}")

    if os.path.exists(OUT):
        os.remove(OUT)
    zf = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
    for root, _dirs, files in os.walk(WORK):
        for f in files:
            full = os.path.join(root, f)
            zf.write(full, os.path.relpath(full, WORK))
    zf.close()
    print("[write]", OUT)


if __name__ == "__main__":
    main()
