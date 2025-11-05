from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
from taxcalc import Policy, Records, Calculator
import pandas as pd
import os
import httpx

app = FastAPI(title="HaloIQ IRS Tax Calculator")

# ---- IRS (PSL) endpoint constants ----
STATUS_MAP = {"single": 1, "married_joint": 2, "married_separate": 3, "head": 4}
PERIODS = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12, "annual": 1}

class Payload(BaseModel):
    gross_amount: float = Field(ge=0)
    filing_status: str
    pay_period: str
    tax_year: int = 2025

# ---- Health check route ----
@app.get("/health")
def health():
    return {"ok": True}

# ---- IRS (PSL) calculator endpoint ----
@app.post("/api/v1/calculate-taxes")
def calculate_taxes(p: Payload):
    annual = p.gross_amount * PERIODS[p.pay_period]
    df = pd.DataFrame({
        "e00200": [annual],                          # wages
        "MARS": [STATUS_MAP[p.filing_status]],       # filing status
        "XTOT": [1],                                 # exemptions (placeholder)
    })
    rec = Records(data=df)
    pol = Policy(); pol.set_year(p.tax_year)
    calc = Calculator(policy=pol, records=rec)
    calc.calc_all()

    federal = float(calc.array("iitax")[0])
    ss = float(calc.array("payrolltax_ss")[0])
    medicare = float(calc.array("payrolltax_hi")[0])
    div = PERIODS[p.pay_period]

    return {
        "success": True,
        "tax_year": p.tax_year,
        "period": p.pay_period,
        "gross_amount": p.gross_amount,
        "taxes": {
            "federal_income_tax": round(federal / div, 2),
            "fica_social_security": round(ss / div, 2),
            "fica_medicare": round(medicare / div, 2),
            "additional_medicare": 0.00
        }
    }

# ---------------------------------------------------------------------------
# TaxUpdate proxy + safe fallback (so HALO IQ can use TaxUpdate first)
# ---------------------------------------------------------------------------

TAX_PROVIDER = os.getenv("TAX_PROVIDER", "placeholder").lower()   # "taxupdate" or "placeholder"
TAXUPDATE_BASE = os.getenv("TAXUPDATE_BASE", "").rstrip("/")      # e.g. https://api.taxupdate.com
TAXUPDATE_KEY  = os.getenv("TAXUPDATE_KEY", "")                   # optional demo key

@app.get("/api/tax/{code}")
async def taxupdate_or_fallback(
    code: str,
    paydate: str = Query(...),
    payperiods: int = Query(...),
    filingstatus: str = Query(...),
    earnings: float = Query(...),
    exemptions: int = 0,
    stateexemptions: int = 0,
    zip: str | None = None,
):
    """
    Try real TaxUpdate API first; if unavailable, return placeholder math so UI still works.
    """
    # --- Try live TaxUpdate API if configured ---
    if TAX_PROVIDER == "taxupdate" and TAXUPDATE_BASE:
        try:
            headers = {"Authorization": f"Bearer {TAXUPDATE_KEY}"} if TAXUPDATE_KEY else {}
            params = {
                "paydate": paydate,
                "payperiods": payperiods,
                "filingstatus": filingstatus,
                "earnings": earnings,
                "exemptions": exemptions,
                "stateexemptions": stateexemptions,
                "zip": zip,
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{TAXUPDATE_BASE}/api/tax/{code}", params=params, headers=headers)
            if r.status_code == 200:
                return r.json()
            else:
                print(f"[TaxUpdate] {r.status_code} response; falling back.")
        except Exception as e:
            print("[TaxUpdate] error:", e)

    # --- Placeholder fallback (flat rates) ---
    c = code.upper()
    if c in ("FIT", "FED", "FEDERAL"):
        rate = 0.10
    elif c in ("SOCIALSECURITY", "SS"):
        rate = 0.062
    elif c in ("MEDICARE", "MED"):
        rate = 0.0145
    else:
        rate = 0.04  # stand-in for state until wired

    tax = round(earnings * rate, 2)
    return {
        "ok": True,
        "provider": "taxupdate" if TAX_PROVIDER == "taxupdate" else "placeholder",
        "tax_type": c,
        "inputs": {
            "paydate": paydate,
            "payperiods": payperiods,
            "filingstatus": filingstatus,
            "earnings": earnings,
            "exemptions": exemptions,
            "stateexemptions": stateexemptions,
            "zip": zip,
        },
        "gross": round(earnings, 2),
        "tax": tax,
        "net": round(earnings - tax, 2),
    }
