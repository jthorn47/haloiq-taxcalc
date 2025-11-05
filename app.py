from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from taxcalc import Policy, Records, Calculator
import pandas as pd

# ---------------------------------------------------------
# App initialization
# ---------------------------------------------------------
app = FastAPI(title="HaloIQ IRS Tax Calculator")

# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------
STATUS_MAP = {
    "single": 1,
    "married_joint": 2,
    "married_separate": 3,
    "head": 4,
}
PERIODS = {
    "weekly": 52,
    "biweekly": 26,
    "semimonthly": 24,
    "monthly": 12,
    "annual": 1,
}

# ---------------------------------------------------------
# Pydantic model for API input
# ---------------------------------------------------------
class Payload(BaseModel):
    gross_amount: float = Field(ge=0)
    filing_status: str
    pay_period: str
    tax_year: int = 2025

# ---------------------------------------------------------
# Root route (Render health check)
# ---------------------------------------------------------
@app.get("/")
def root():
    # ✅ Render requires this endpoint for health
    return {"ok": True, "service": "haloiq-taxcalc"}

# ---------------------------------------------------------
# Explicit health check route
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}

# ---------------------------------------------------------
# IRS Federal Tax Calculation Endpoint
# ---------------------------------------------------------
@app.post("/api/v1/calculate-taxes")
def calculate_taxes(p: Payload):
    try:
        annual = p.gross_amount * PERIODS[p.pay_period]
        df = pd.DataFrame({
            "e00200": [annual],
            "MARS": [STATUS_MAP[p.filing_status]],
            "XTOT": [1],
        })

        rec = Records(data=df)
        pol = Policy()
        calc = Calculator(policy=pol, records=rec)
        calc.calc_all()

        results = calc.array("iitax")
        annual_tax = float(results[0])
        per_period_tax = round(annual_tax / PERIODS[p.pay_period], 2)
        net = round(p.gross_amount - per_period_tax, 2)

        return {
            "ok": True,
            "provider": "taxupdate",
            "tax_type": "FIT",
            "inputs": p.dict(),
            "gross": p.gross_amount,
            "tax": per_period_tax,
            "net": net,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------------------------------------------------------
# Quick browser test endpoint
# ---------------------------------------------------------
@app.get("/api/tax/{tax_type}")
def quick_tax(
    tax_type: str,
    paydate: str = Query(...),
    payperiods: int = Query(...),
    filingstatus: str = Query(...),
    earnings: float = Query(...),
):
    try:
        tax = round(earnings * 0.10, 2)
        net = round(earnings - tax, 2)
        return {
            "ok": True,
            "provider": "taxupdate",
            "tax_type": tax_type,
            "inputs": {
                "paydate": paydate,
                "payperiods": payperiods,
                "filingstatus": filingstatus,
                "earnings": earnings,
            },
            "gross": earnings,
            "tax": tax,
            "net": net,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
