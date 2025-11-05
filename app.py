from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from taxcalc import Policy, Records, Calculator
import pandas as pd

app = FastAPI(title="HaloIQ IRS Tax Calculator")

# --- IRS (PSL) endpoint constants ---
STATUS_MAP = {"single": 1, "married_joint": 2, "married_separate": 3, "head": 4}
PERIODS = {"weekly": 52, "biweekly": 26, "semimonthly": 24, "monthly": 12, "annual": 1}

class Payload(BaseModel):
    gross_amount: float = Field(ge=0)
    filing_status: str
    pay_period: str
    tax_year: int = 2025

# --- Health check route ---
@app.get("/health")
def health():
    return {"ok": True}

# --- IRS (PSL) calculator endpoint ---
@app.post("/api/v1/calculate-taxes")
def calculate_taxes(p: Payload):
    annual = p.gross_amount * PERIODS[p.pay_period]

    df = pd.DataFrame({
        "e00200": [annual],                         # wages
        "MARS": [STATUS_MAP[p.filing_status]],      # filing status
        "XTOT": [1],                                # exemptions (placeholder)
    })

    rec = Records(data=df)
    pol = Policy()
    pol.set_year(p.tax_year)

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

# --- TaxUpdate-style shim endpoints ---
# These mimic TaxUpdate API so your Edge Function can call them directly.

@app.get("/api/tax/{code}")
def shim_tax(
    code: str,
    paydate: str = Query(...),          # YYYY-MM-DD (placeholder)
    payperiods: int = Query(...),       # 52, 26, 24, 12, 1 (placeholder)
    filingstatus: str = Query(...),     # single|married_joint|... (placeholder)
    earnings: float = Query(...),
    exemptions: int = 0,
    stateexemptions: int = 0,
    zip: str | None = None,
):
    code = code.upper()

    # ----- PLACEHOLDER RATES (replace with real logic later) -----
    if code in ("FIT", "FED", "FEDERAL"):
        rate = 0.10
    elif code in ("SOCIALSECURITY", "SS"):
        rate = 0.062
    elif code in ("MEDICARE", "MED"):
        rate = 0.0145
    else:
        # e.g., state codes like 'CA', 'NY' until state logic is wired
        rate = 0.04
    # -------------------------------------------------------------

    tax = round(earnings * rate, 2)
    return {
        "ok": True,
        "provider": "taxupdate",
        "tax_type": code,
        "inputs": {
            "paydate": paydate,
            "payperiods": payperiods,
            "filingstatus": filingstatus,
            "earnings": round(earnings, 2),
            "exemptions": exemptions,
            "stateexemptions": stateexemptions,
            "zip": zip,
        },
        "gross": round(earnings, 2),
        "tax": tax,
        "net": round(earnings - tax, 2),
    }
