from fastapi import FastAPI
from pydantic import BaseModel, Field
from taxcalc import Policy, Records, Calculator
import pandas as pd

app = FastAPI(title="HaloIQ IRS Tax Calculator")

STATUS_MAP = {"single":1, "married_joint":2, "married_separate":3, "head":4}
PERIODS = {"weekly":52, "biweekly":26, "semimonthly":24, "monthly":12, "annual":1}

class Payload(BaseModel):
    gross_amount: float = Field(ge=0)
    filing_status: str
    pay_period: str
    tax_year: int = 2025

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/v1/calculate-taxes")
def calculate_taxes(p: Payload):
    annual = p.gross_amount * PERIODS[p.pay_period]
    df = pd.DataFrame({"e00200":[annual],"MARS":[STATUS_MAP[p.filing_status]],"XTOT":[1]})
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
            "federal_income_tax": round(federal/div,2),
            "fica_social_security": round(ss/div,2),
            "fica_medicare": round(medicare/div,2),
            "additional_medicare": 0.00
        }
    }
