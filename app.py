from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import math

app = FastAPI(title="NBC GARUDA Calculator")

# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

class InputPayload(BaseModel):
    age: Optional[float] = Field(None, ge=0, le=120)
    gcs: Optional[int] = Field(None, ge=3, le=15)
    dome: Optional[float] = Field(None, ge=0, le=50)
    neck: Optional[float] = Field(None, ge=0, le=20)

    htn: Optional[int] = None
    cvd: Optional[int] = None
    smoke: Optional[int] = None
    famHist: Optional[int] = None
    wfns: Optional[int] = None
    hemiparesis: Optional[int] = None
    ruptured: Optional[int] = None
    dm: Optional[int] = None
    location: Optional[str] = None
    daughter: Optional[int] = None
    ptosis: Optional[int] = None
    seizure: Optional[int] = None
    multiple: Optional[int] = None
    iom: Optional[int] = None


def _val(x):
    if x is None:
        return 0.0, True
    try:
        return float(x), False
    except:
        return 0.0, True

def _sigmoid(z):
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    else:
        ez = math.exp(z)
        return ez / (1.0 + ez)

def _location_coef(loc):
    mapping = {
        "acha": 1.272,
        "acom": -0.608,
        "basilar": 0.383,
        "ica": -0.019,
        "mca": -1.061,
        "pcoa": -0.411,
    }
    if loc is None or loc not in mapping:
        return 0.0, True
    return mapping[loc], False

def compute_outcomes(p: InputPayload) -> Dict[str, Any]:
    age, m_age = _val(p.age)
    gcs, m_gcs = _val(p.gcs)
    dome, m_dome = _val(p.dome)
    neck, m_neck = _val(p.neck)

    htn, _ = _val(p.htn)
    cvd, _ = _val(p.cvd)
    smoke, _ = _val(p.smoke)
    fam, _ = _val(p.famHist)
    wfns, _ = _val(p.wfns)
    hemi, _ = _val(p.hemiparesis)
    rupt, _ = _val(p.ruptured)
    dm, _ = _val(p.dm)
    daughter, _ = _val(p.daughter)
    ptosis, _ = _val(p.ptosis)
    seizure, _ = _val(p.seizure)
    multiple, _ = _val(p.multiple)
    iom, _ = _val(p.iom)

    gcs_lt15 = 1.0 if (not m_gcs and gcs <= 14) else 0.0
    dn_ratio = (dome / neck) if (not m_dome and not m_neck and neck > 0) else 0.0
    neck_gt4 = 1.0 if (not m_neck and neck > 4) else 0.0
    loc_coef, _ = _location_coef(p.location)

    z1 = -5.073 + 0.022 * age + 1.008 * htn + 0.525 * wfns + 0.061 * dome
    z2 = -1.198 + (-0.019) * age + 1.678 * cvd + (-1.878) * smoke + 2.157 * fam + 1.653 * gcs_lt15 + (-1.119) * iom + 0.059 * dome + (-0.233) * dn_ratio
    z3 = 2.19 + (-0.013) * age + (-0.626) * hemi + (-0.493) * wfns + (-0.703) * rupt
    z4 = 2.781 + (-0.043) * age + 1.439 * dm + (-1.363) * gcs_lt15 + loc_coef + (-0.856) * daughter
    z5 = 3.198 + (-0.033) * age + (-1.143) * dm + (-0.94) * ptosis + (-0.977) * seizure + 0.621 * multiple + (-0.029) * dome + (-0.232) * dn_ratio
    z6 = 3.334 + (-0.033) * age + (-1.0) * cvd + (-0.517) * gcs_lt15 + 0.843 * iom + (-1.542) * rupt + (-0.179) * dome + 0.646 * neck_gt4

    p1, p2, p3, p4, p5, p6 = map(_sigmoid, [z1, z2, z3, z4, z5, z6])

    return {
        "mortality_coil": round(p1 * 100, 1),
        "mortality_clip": round(p2 * 100, 1),
        "good_gose_coil": round(p3 * 100, 1),
        "good_gose_clip": round(p4 * 100, 1),
        "gcs_recovery_coil": round(p5 * 100, 1),
        "gcs_recovery_clip": round(p6 * 100, 1),
        "derived": {
            "gcs_lt15": gcs_lt15,
            "dn_ratio": round(dn_ratio, 2),
            "neck_gt4": neck_gt4,
        },
    }

@app.post("/api/predict")
async def predict(inp: InputPayload):
    return compute_outcomes(inp)
