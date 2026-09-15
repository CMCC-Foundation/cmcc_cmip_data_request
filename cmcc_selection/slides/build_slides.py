#!/usr/bin/env python
"""Fill slides 2 and 3 of dr.pptx (CMCC AR7-FT Data Request 1 and 2).

Keeps every template shape of each slide (header band, title, rules, logo) and
replaces only the colleague's placeholder body text box with composed content.
Writes dr_filled.pptx; the original dr.pptx is left untouched.
"""
import os, re, shutil, zipfile

SRC = "/Users/giovanniconti/Documents/dr_cmip7/cmcc_selection/slides/dr.pptx"
OUT = "/Users/giovanniconti/Documents/dr_cmip7/cmcc_selection/slides/dr_filled.pptx"
WORK = "/private/tmp/claude-501/-Users-giovanniconti-Documents-dr-cmip7/56a7b982-1a6d-4372-b98e-a64d0dc2cbc8/scratchpad/build"

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


def para(runs, algn="l", after=0, before=0, line=100, bullet=None, marL=0, indent=0):
    bu = '<a:buNone/>'
    if bullet:
        bu = (f'<a:buClr><a:srgbClr val="{BLUE}"/></a:buClr>'
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


# ------------------------------------------------------------------ slide (1)
def slide1_body():
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
    # stacked bar: 436 mapped / 67 derivable / 350 true gap of 853
    x, w, y = 6.93, 5.55, 3.62
    seg = [(436, BLUE), (67, BLUE_L), (350, ORANGE)]
    for n, c in seg:
        ww = w * n / 853.0
        s.append(rect(x, y, ww, 0.26, c))
        x += ww
    rows = [("436", BLUE, "produced today — CMOR name maps to a raw model field"),
            ("67", BLUE_L, "derivable — slice or average of a field already "
                           "stored, no extra storage"),
            ("350", ORANGE, "true gap — no model output yet: add, derive, "
                            "enable or drop")]
    yy = 4.06
    for num, color, label in rows:
        s.append(rect(6.93, yy + 0.07, 0.13, 0.13, color))
        s.append(txbox(7.16, yy - 0.05, 0.72, 0.34,
                       [para([run(num, sz=1450, b=1, color=NAVY, font=HEAD)])]))
        s.append(txbox(7.92, yy - 0.03, 4.56, 0.62,
                       [para([run(label, sz=1150)], line=104)]))
        yy += 0.60
    s.append(txbox(6.93, 5.72, 5.55, 0.62,
                   [para([run("Gaps by realm: land 96, atmos 65, ocean BGC 55, "
                              "aerosol 49, ocean 34, atmos chemistry 23, sea ice 18, "
                              "land ice 10. Aerosol and atmospheric chemistry are "
                              "almost entirely gaps (2 of 75 producible).",
                              sz=1100, color=GREY, i=1)], line=104)]))

    s.append(footnote(6.72, [
        "853 counts one entry per requested variable × frequency × statistic "
        "(the unit the model output configuration needs); the same field at daily and "
        "monthly is one raw model variable, hence 660 distinct CMOR names.",
    ]))
    return s


# ------------------------------------------------------------------ slide (2)
def slide2_body():
    s = [kicker("Storage cost on the CMCC-ESM3 grid — GB per simulated "
                "model-year, uncompressed on-disk size")]
    s += stat_cards([("213", "GB/yr", "produced today — about 2× a CMIP6 "
                                      "model-year"),
                     ("+224", "GB/yr", "extra storage to cover every true gap"),
                     ("437", "GB/yr", "full request ≈ 4.4× CMIP6; "
                                      "derivable variables are free")])

    s.append(col_head(0.85, 3.16, "Where the cost sits", w=6.10))
    s.append(bullets(0.85, 3.58, 6.10, 2.60, [
        "Ocean 3-hourly is the whole story: 174 of the 224 GB gap (daily 41, "
        "monthly 10)",
        "Two fields alone are 76 % of the gap — ficeberg 86 and hfrunoffds "
        "85 GB/yr",
        "One 3-D ocean field at 3hr ≈ 92 GB/yr; the same field at 3-D atmos "
        "≈ 33 GB/yr",
        "6-hourly and 1-hourly requests have no gaps — 82 and 14 GB/yr, "
        "produced today",
    ], sz=1250))
    s.append(rect(0.85, 5.86, 6.10, 0.52, CARD, rad=0.08))
    s.append(txbox(0.97, 5.86, 5.86, 0.52,
                   [para([run("Trimming lever: ", sz=1200, b=1,
                              color=NAVY, font=HEAD),
                          run("ocean sub-daily 3-D output", sz=1200, b=1,
                              color=ORANGE, font=HEAD)])], anchor="ctr"))

    # bar comparison
    s.append(col_head(7.45, 3.16, "GB per model-year", w=5.03))
    bars = [("CMIP6 reference", [(100, GREY_L)], "100"),
            ("Produced today", [(213, BLUE)], "213"),
            ("Full request", [(213, BLUE), (224, ORANGE)], "437")]
    y = 3.66
    for label, segs, total in bars:
        s.append(txbox(7.45, y - 0.02, 5.03, 0.28,
                       [para([run(label, sz=1100, color=GREY)])]))
        x = 7.45
        for val, c in segs:
            w = 4.60 * val / 437.0
            s.append(rect(x, y + 0.28, w, 0.30, c))
            x += w
        s.append(txbox(x + 0.06, y + 0.26, 1.00, 0.32,
                       [para([run(total, sz=1250, b=1, color=NAVY, font=HEAD)])]))
        y += 0.80
    s.append(txbox(7.45, 6.06, 5.03, 0.32,
                   [para([run("blue = produced   ·   orange = still to be "
                              "produced", sz=1000, color=GREY, i=1)])]))

    s.append(footnote(6.48, [
        "Grid: CAM/CLM spectral element ncol 48600 × L58, NEMO 360×291 "
        "× L75, float32; calibrated on a real B1850 run and validated against "
        "its files (thetao monthly 377 MB/yr, zos 5 MB/yr). Archived, deflated size "
        "≈ half.",
        "Gaps are tracked as open rows in the per-component CMOR↔raw lookup "
        "tables (386 to resolve): fill the raw model name and the variable enters "
        "the production list automatically.",
    ]))
    return s


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
     "pipeline cannot silently produce a shorter list. That gives 853 requests, i.e. 660 "
     "distinct CMOR variables across frequencies. Against the CMCC-ESM3 output we "
     "then have 436 already producible, 67 derivable from fields we already store, "
     "and 350 true gaps - concentrated in aerosol and atmospheric chemistry, land "
     "carbon and ocean biogeochemistry."),
 3: ("Volumes are per simulated model-year on the CMCC-ESM3 grid, uncompressed. We "
     "produce about 213 GB per model-year today, roughly twice a CMIP6 model-year; "
     "the full request would be 437 GB, about 4.4 times CMIP6. Derivable variables "
     "add nothing because they are slices of stored fields. The cost is extremely "
     "concentrated: 174 of the 224 GB gap is ocean 3-hourly, and two fields - "
     "ficeberg and hfrunoffds - are 76 % of it. So the decision to take is about "
     "ocean sub-daily 3-D output, not about 350 variables. The estimate is "
     "calibrated on a real B1850 run and validated against its files. Remaining "
     "gaps are tracked as open rows in the lookup tables that map CMOR names to raw "
     "model fields."),
}


def fill(slide_xml, body_shapes):
    """Drop the placeholder body text box, append the composed shapes."""
    k = slide_xml.index("spAutoFit")
    start = slide_xml.rindex("<p:sp>", 0, k)
    end = slide_xml.index("</p:sp>", k) + len("</p:sp>")
    assert "Summary on selected opportunities" in slide_xml[start:end], \
        "the shape found is not the colleague's placeholder"
    x = slide_xml[:start] + slide_xml[end:]
    return x.replace("</p:spTree>", "".join(body_shapes) + "</p:spTree>")


def set_notes(path, text):
    x = open(path).read()
    # replace the text of the first body placeholder paragraph block
    body = re.search(r'(<p:sp>(?:(?!</p:sp>).)*?type="body".*?</p:sp>)', x, re.S)
    if not body:
        return False
    new_p = ('<a:p><a:pPr rtl="0"><a:buNone/></a:pPr>'
             f'<a:r><a:rPr lang="en-GB" sz="1200"/><a:t>{esc(text)}</a:t></a:r></a:p>')
    sp = body.group(1)
    sp2 = re.sub(r'(<a:lstStyle/>).*?(</p:txBody>)', r'\1' + new_p + r'\2', sp, flags=re.S)
    open(path, "w").write(x.replace(sp, sp2))
    return True


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    with zipfile.ZipFile(SRC) as z:
        z.extractall(WORK)

    for n, builder in ((2, slide1_body), (3, slide2_body)):
        p = f"{WORK}/ppt/slides/slide{n}.xml"
        with open(p) as f:                      # read BEFORE opening for write
            filled = fill(f.read(), builder())
        with open(p, "w") as f:
            f.write(filled)
        print(f"slide{n}.xml filled")

    for n, text in NOTES.items():
        rels = open(f"{WORK}/ppt/slides/_rels/slide{n}.xml.rels").read()
        m = re.search(r'notesSlide(\d+)\.xml', rels)
        if m and set_notes(f"{WORK}/ppt/notesSlides/notesSlide{m.group(1)}.xml", text):
            print(f"notes for slide{n} written")

    if os.path.exists(OUT):
        os.remove(OUT)
    zf = zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED)
    for root, _dirs, files in os.walk(WORK):
        for f in files:
            full = os.path.join(root, f)
            zf.write(full, os.path.relpath(full, WORK))
    zf.close()
    print("wrote", OUT)


if __name__ == "__main__":
    main()
