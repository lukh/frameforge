#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, os, csv, math, re, sys
from typing import Dict, Any, Optional

def read_csv_rows(path: str):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean_row = {}
            for k, v in row.items():
                key = k.strip() if isinstance(k, str) else k
                if isinstance(v, str):
                    val = v.strip()
                else:
                    val = v
                clean_row[key] = val
            yield clean_row

def parse_fraction(s):
    if s is None or s == "":
        return None
    s = str(s).strip()
    if s in ("-", "–", "—", "NA", "N/A", ".", "nan"):
        return None
    if re.match(r'^\d+\s+\d+/\d+$', s):
        parts = s.split()
        whole = float(parts[0])
        num, den = parts[1].split('/')
        return whole + float(num)/float(den)
    if re.match(r'^\d+/\d+$', s):
        num, den = s.split('/')
        return float(num)/float(den)
    try:
        return float(s)
    except:
        try:
            return float(s.replace(',', '.'))
        except:
            return None

def clean_val(v):
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v):
            return None
        return v
    s = str(v).strip()
    if s in ("", "-", "–", "—", "NA", "N/A", "."):
        return None
    s2 = s.replace(',', '.')
    frac = parse_fraction(s2)
    if frac is not None:
        if '/' in s:
            return frac
        return frac
    return s2

def parse_designation_for_hss(designation):
    if not designation:
        return None
    d = designation.upper().replace("HSS", "").replace(" ", "")
    m = re.match(r'(\d+\.?\d*)X(\d+\.?\d*)X(.+)$', d, re.IGNORECASE)
    if not m:
        nums = re.findall(r'\d+\/\d+|\d+\.\d+|\d+', d)
        if len(nums) >= 3:
            h = parse_fraction(nums[0])
            b = parse_fraction(nums[1])
            t = parse_fraction(nums[2])
            return {"H": h, "B": b, "t": t}
        return None
    h = parse_fraction(m.group(1))
    b = parse_fraction(m.group(2))
    t = parse_fraction(m.group(3))
    return {"H": h, "B": b, "t": t}

def get_val(row: Dict[str, Any], col: Optional[str], default: Optional[str] = None) -> Optional[str]:
    if not col:
        return default
    if col not in row:
        return default
    v = row[col]
    cv = clean_val(v)
    if cv is None:
        return default
    if isinstance(cv, float):
        if abs(cv - round(cv)) < 1e-9:
            return str(int(round(cv)))
        else:
            s = ("{:.5f}".format(cv)).rstrip('0').rstrip('.')
            return s
    return str(cv)

def coalesce(*vals):
    for v in vals:
        if v not in (None, "", "None", "nan"):
            return v
    return None

def sanitize_key(s: str) -> str:
    return s.strip()


def format_number(s):
    try:
        return f"{float(s):.3f}"
    except:
        return "0.0"

def build_sizes(fam_name, rows, cfg: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    sizes = {}
    des_col = cfg.get("designation_col", "Designation")
    h_col = cfg.get("height_col")
    w_col = cfg.get("width_col")
    t_col = cfg.get("thickness_col")
    tw_col = cfg.get("web_thickness_col")
    tf_col = cfg.get("flange_thickness_col")
    r1_col = cfg.get("radius1_col")
    r2_col = cfg.get("radius2_col")
    wgt_col = cfg.get("weight_col", "W")
    key_override = cfg.get("size_key")
    filters: Dict[str, Any] = cfg.get("filters", {})
    # fam_name = cfg.get("family_name", "").lower()

    for row in rows:
        # --- Filtres ---
        skip = False
        for k, v in filters.items():
            if str(row.get(k, "")).strip() != str(v):
                skip = True
                break
        if skip:
            continue

        if cfg.get("filter_mode") == "equal_legs":
            dval = clean_val(row.get("d"))
            bval = clean_val(row.get("b"))
            if dval is None or bval is None or float(dval) != float(bval):
                continue
        elif cfg.get("filter_mode") == "unequal_legs":
            dval = clean_val(row.get("d"))
            bval = clean_val(row.get("b"))
            if dval is None or bval is None or float(dval) == float(bval):
                continue
        

        # --- Désignation ---
        des = get_val(row, des_col)
        if not des and key_override:
            des = get_val(row, key_override)
        if not des:
            continue

        # --- Parsing spécial HSS ---
        parsed_hss = None
        if des.upper().startswith("HSS"):
            parsed_hss = parse_designation_for_hss(des)

        # --- Dimensions principales ---
        h = get_val(row, h_col)
        w = get_val(row, w_col)
        if parsed_hss:
            if not h and parsed_hss.get("H"):
                h = format_number(parsed_hss["H"])
            if not w and parsed_hss.get("B"):
                w = format_number(parsed_hss["B"])

        if cfg.get("filter_mode") == "square_hss":
            print(format_number(w),format_number(h))
            if format_number(w) != format_number(h):
                continue
        elif cfg.get("filter_mode") == "rectangular_hss":
            if format_number(w) == format_number(h):
                continue

        # --- Épaisseur ---
        t = get_val(row, t_col)
        if t is None:
            t = coalesce(get_val(row, tw_col), get_val(row, tf_col))
        if t is None and parsed_hss and parsed_hss.get("t"):
            t = format_number(parsed_hss["t"])

        # --- Rayons et poids ---
        r1 = get_val(row, r1_col, default=None)
        r2 = get_val(row, r2_col, default=None)
        wgt = get_val(row, wgt_col)

        # Auto-fill radii si manquants
        t_num = None
        try:
            if t is not None:
                t_num = float(str(t).replace(',', '.'))
        except:
            pass

        if (not r1 or r1 in ("0", None)) and (not r2 or r2 in ("0", None)):
            if "hss" in fam_name or "hollow" in fam_name or "pipe" in fam_name:
                if t_num:
                    r1 = format_number(2 * t_num)
                    r2 = format_number(1.5 * t_num)
            elif any(x in fam_name for x in ["hea","heb","hem","ipe","ipn","wide flange","w","upn","upe"]):
                if tw_col and row.get(tw_col):
                    r1 = get_val(row, tw_col)
                elif t is not None:
                    r1 = t
                if tf_col and row.get(tf_col):
                    r2 = get_val(row, tf_col)
                elif t is not None:
                    r2 = t
            elif "angle" in fam_name or "leg" in fam_name:
                if t_num:
                    r1 = format_number(2 * t_num)
                    r2 = format_number(1.5 * t_num)

        # --- Clé de taille ---
        size_key = sanitize_key(des)
        shape = {}
        if h is not None:      shape["Height"] = str(h)
        if w is not None:      shape["Width"] = str(w)
        if t is not None:      shape["Thickness"] = str(t)
        if r1 is not None:     shape["Radius1"] = str(r1)
        if r2 is not None:     shape["Radius2"] = str(r2)
        if wgt is not None:    shape["Weight"] = str(wgt)

        if any(k in shape for k in ("Height","Width","Thickness")):
            sizes[size_key] = shape

    return sizes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", required=True, help="Path to existing metric JSON (used for family keys)")
    ap.add_argument("--csv-dir", required=True, help="Directory containing AISC CSV files")
    ap.add_argument("--mapping", required=True, help="JSON mapping that tells the script which CSV/columns to use per family")
    ap.add_argument("--out", required=True, help="Output JSON path for the AISC file")
    args = ap.parse_args()

    with open(args.metric, "r", encoding="utf-8") as f:
        metric = json.load(f)
    with open(args.mapping, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    out_data = {}
    families = list(metric.keys())

    for fam in families:
        fam_cfg = mapping["families"].get(fam)
        if not fam_cfg:
            print(f"[WARN] Family not mapped in config, skipping: {fam}", file=sys.stderr)
            continue

        csv_path = os.path.join(args.csv_dir, fam_cfg["csv"])
        if not os.path.isfile(csv_path):
            print(f"[WARN] CSV not found for family {fam}: {csv_path}", file=sys.stderr)
            continue

        rows = list(read_csv_rows(csv_path))
        sizes = build_sizes(fam.lower(), rows, fam_cfg)

        out_data[fam] = {
            "norm": fam_cfg.get("norm", "AISC"),
            "unit": fam_cfg.get("unit", "in"),
            "fillet": bool(fam_cfg.get("fillet", metric.get(fam, {}).get("fillet", True))),
            "sizes": sizes
        }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=4)
    print(f"[OK] Wrote: {args.out}")

if __name__ == "__main__":
    main()
