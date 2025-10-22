import json
import uuid
import random
from typing import Dict, Any, Optional, List
from .llm import chat_json
from .emotion_model import EmotionGenerator, EmotionProfile

# ===== Enumerations (EN) =====
GENDER_OPTIONS = ["Male", "Female", "Non-binary/Other"]
EDU_OPTIONS = ["Middle school", "High school", "Vocational/Trade", "College", "Master's", "PhD"]
INCOME_OPTIONS = ["<USD 1k/mo", "USD 1k-2k/mo", "USD 2k-5k/mo", "USD 5k-10k/mo", "USD 10k-20k/mo", ">USD 20k/mo"]

# Common English names (balanced & realistic)
EN_FIRST_NAMES_M = [
    "James","John","Robert","Michael","William","David","Richard","Joseph",
    "Thomas","Charles","Christopher","Daniel","Matthew","Anthony","Mark","Paul",
    "Andrew","Joshua","Steven","Kevin","Brian","George","Edward","Timothy",
    "Jason","Jeffrey","Ryan","Jacob","Gary","Nicholas","Eric","Jonathan",
    "Stephen","Larry","Justin","Scott","Brandon","Benjamin","Samuel","Gregory"
]
EN_FIRST_NAMES_F = [
    "Mary","Patricia","Jennifer","Linda","Elizabeth","Barbara","Susan","Jessica",
    "Sarah","Karen","Nancy","Lisa","Margaret","Betty","Sandra","Ashley","Dorothy",
    "Kimberly","Emily","Donna","Michelle","Carol","Amanda","Melissa","Deborah",
    "Stephanie","Rebecca","Sharon","Laura","Cynthia","Kathleen","Amy","Shirley",
    "Angela","Helen","Anna","Brenda","Pamela","Nicole","Emma","Olivia","Sophia"
]
EN_LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
    "Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill","Flores"
]

def _weighted_choice(d: Dict[str, float], default: str) -> str:
    if not d:
        return default
    items = list(d.items())
    total = sum(max(0.0, float(w)) for _, w in items)
    if total <= 0:
        return default
    r = random.random() * total
    acc = 0.0
    for k, w in items:
        acc += max(0.0, float(w))
        if r <= acc:
            return k
    return items[-1][0]

def _sample_en_name(gender_hint: Optional[str] = None) -> str:
    if gender_hint and gender_hint.lower().startswith("f"):
        first = random.choice(EN_FIRST_NAMES_F)
    elif gender_hint and gender_hint.lower().startswith("m"):
        first = random.choice(EN_FIRST_NAMES_M)
    else:
        first = random.choice(EN_FIRST_NAMES_M + EN_FIRST_NAMES_F)
    last = random.choice(EN_LAST_NAMES)
    # 15% chance to have middle initial
    if random.random() < 0.15:
        return f"{first} {chr(random.randint(65,90))}. {last}"
    return f"{first} {last}"

SYS = (
    "You are a strict persona generator. Output must be in ENGLISH only. "
    "All names must be realistic English names (first + last), no placeholders, no duplicates. "
    "Align personas to the given environment and constraints, and reflect demographic diversity."
)

SINGLE_USER_TPL = """Generate ONE persona JSON in ENGLISH. Fill missing fields sensibly.
Return ONLY a JSON object, no code block, no extra text.

Context (optional): {hints}

Required JSON schema:
{{
  "name": "English name (First Last), unique",
  "gender": "Male/Female/Non-binary (or similar in English)",
  "age": 14-75 (integer),
  "occupation": "Realistic job aligned with the environment",
  "income_level": "Income in English, e.g., 'USD 2k-5k/mo' or 'Dependent on parents'",
  "education": "Education level in English",
  "description": "1-2 sentences in English",
  "initial_memory": ["at least 3 short English items"],
  "initial_state": {{"location": "must be one of environment locations if known, else 'Start'", "mood": "e.g., calm/curious/anxious", "emotion": "emotion profile with numerical values"}}
}}"""

BATCH_USER_TPL_ENV = """Generate {n} persona JSON objects in ENGLISH only.

[Environment Title] {title}
[Environment Description] {prompt}
[Environment Rules] {rules}
[Population Constraints] {constraints}

Hard requirements:
1) Names must be realistic English (First Last), ALL UNIQUE, no placeholder names.
2) Gender & age structure should approximately follow gender_ratio / age_buckets. If absent, assume ~50/50 gender, small share non-binary, plausible age distribution.
3) Occupation/role distribution should roughly follow role_mix; if absent, infer realistic roles from the environment (e.g., high school = students/teachers/admin/security/cleaning/cafeteria).
4) initial_state.location must be chosen from the environment's location list (if not provided, infer 6-12 plausible locations first and then use them).
5) Every field must be in English. Avoid collapse to the same gender or job.

Return ONLY a JSON ARRAY of length {n}, each element with the schema above. No explanation, no code fences.
"""

# ==== Public APIs ====

async def generate_persona_default(
    name: str,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    occupation: Optional[str] = None,
    income_level: Optional[str] = None,
    education: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    hints = {k: v for k, v in {
        "name": name, "gender": gender, "age": age, "occupation": occupation,
        "income_level": income_level, "education": education, "description": description,
    }.items() if v is not None}

    data = await chat_json(
        system=SYS,
        messages=[{"role": "user", "content": SINGLE_USER_TPL.format(
            hints=json.dumps(hints, ensure_ascii=False, indent=2) if hints else "(none)"
        )}],
        temperature=0.5,
        max_tokens=800,
    )
    return _normalize_persona(data, fallback_name=name)

async def generate_personas_for_environment(
    count: int,
    env_spec: Dict[str, Any],
    diversity_hint: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Environment-driven persona generation in EN. Falls back to local synthesis if LLM fails."""
    if count <= 0:
        return []

    title = env_spec.get("title") or "Environment"
    prompt = env_spec.get("prompt") or ""
    rules = env_spec.get("rules") or []
    constraints = constraints or {}
    constraints_text = json.dumps(constraints, ensure_ascii=False)

    # 1) Try LLM
    arr: List[Dict[str, Any]] = []
    try:
        arr = await chat_json(
            system=SYS,
            messages=[{"role": "user", "content": BATCH_USER_TPL_ENV.format(
                n=count, title=title, prompt=prompt,
                rules="\n".join(f"- {r}" for r in rules) if rules else "(none)",
                constraints=constraints_text
            ) + (f"\n[Additional diversity hint] {diversity_hint}" if diversity_hint else "")}],
            temperature=0.6,
            max_tokens=min(1500 + count * 220, 6000),
        )
        if not isinstance(arr, list):
            arr = []
    except Exception:
        arr = []

    personas = [_normalize_persona(x) for x in arr][:count]

    # 2) Fallback if not enough
    if len(personas) < count:
        personas.extend(_bootstrap_personas(count - len(personas), constraints, env_spec))

    # 3) Local rebalancing & fixes
    personas = _rebalance_and_fix(personas, count, constraints, env_title=title)

    return personas

# ==== Internals ====

def _normalize_persona(data: Dict[str, Any], fallback_name: Optional[str] = None) -> Dict[str, Any]:
    def _get(k, default):
        v = data.get(k)
        return v if v not in (None, "") else default

    name = str(_get("name", fallback_name or "Unnamed")).strip()
    # Avoid ultra-common placeholders; enforce English
    if name.lower() in {"zhang wei", "wang wei", "li na", "li lei", "test user"} or " " not in name:
        name = _sample_en_name(data.get("gender"))

    gender = str(_get("gender", random.choice(["Male","Female"]))).strip().title()
    if gender.lower().startswith("m"): gender = "Male"
    elif gender.lower().startswith("f"): gender = "Female"
    else: gender = "Non-binary/Other"

    age = _get("age", random.randint(18, 55))
    try:
        age = int(age)
    except Exception:
        age = random.randint(18, 55)

    occupation = str(_get("occupation", "Service worker")).strip()
    income = str(_get("income_level", "USD 2k-5k/mo")).strip()
    education = str(_get("education", random.choice(["High school","College","Master's"]))).strip()
    description = str(_get("description", "Ordinary resident; cooperative and family-oriented.")).strip()

    init_mem = _get("initial_memory", ["Cares about rules","Sensitive to peer opinions","Willing to cooperate"])
    if not isinstance(init_mem, list):
        init_mem = [str(init_mem)]
    init_mem = [str(x).strip() for x in init_mem if str(x).strip()]

    init_state = _get("initial_state", {"location": "Start", "mood": "calm"})
    if not isinstance(init_state, dict):
        init_state = {"location": "Start", "mood": "calm"}
    init_state.setdefault("location", "Start")
    init_state.setdefault("mood", "calm")
    
    # 生成初始情绪画像
    if "emotion" not in init_state or not isinstance(init_state.get("emotion"), dict):
        # 基于mood和人格描述生成情绪
        mood_str = init_state.get("mood", "calm")
        personality_desc = description
        
        # 生成情绪画像
        emotion = EmotionGenerator.generate_from_context(
            f"Initial mood: {mood_str}, Personality: {personality_desc}",
            {"description": personality_desc}
        )
        init_state["emotion"] = emotion.to_dict()

    return {
        "id": f"agent_{uuid.uuid4().hex}",
        "name": name,
        "gender": gender,
        "age": age,
        "occupation": occupation,
        "income_level": income,
        "education": education,
        "description": description,
        "initial_memory": init_mem,
        "initial_state": init_state,
    }

def _bootstrap_personas(n: int, constraints: Dict[str, Any], env_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Local English fallback generator (no LLM)."""
    res: List[Dict[str, Any]] = []
    gender_ratio = constraints.get("gender_ratio") or {"Male": 0.49, "Female": 0.49, "Non-binary/Other": 0.02}
    age_buckets = constraints.get("age_buckets") or {"14-18":0.05,"19-25":0.2,"26-40":0.35,"41-60":0.25,"61-75":0.15}
    role_mix = constraints.get("role_mix") or {}
    locs = constraints.get("locations") or _infer_locations_from_env(env_spec)

    def _sample_age() -> int:
        bucket = _weighted_choice(age_buckets, "26-40")
        lo, hi = bucket.split("-")
        return random.randint(int(lo), int(hi))

    default_roles = ["High school student","Teacher","Administrator","Security staff","Cleaner","Cafeteria worker","Volunteer","Retail clerk","Passenger"]
    for _ in range(n):
        g = _weighted_choice(gender_ratio, "Male")
        role = _weighted_choice(role_mix, random.choice(default_roles))
        nm = _sample_en_name(g)
        res.append({
            "id": f"agent_{uuid.uuid4().hex}",
            "name": nm,
            "gender": g,
            "age": _sample_age(),
            "occupation": role,
            "income_level": random.choice(INCOME_OPTIONS),
            "education": random.choice(EDU_OPTIONS[1:]),
            "description": f"{role}; ordinary resident; cooperative.",
            "initial_memory": ["Follows rules", "Seeks social acceptance", "Watches authority signals"],
            "initial_state": _generate_initial_state_with_emotion(random.choice(locs) if locs else "Start", random.choice(["calm","neutral","curious"]), f"{role}; ordinary resident; cooperative."),
        })
    return res

def _generate_initial_state_with_emotion(location: str, mood: str, personality: str) -> Dict[str, Any]:
    """生成包含情绪画像的初始状态"""
    emotion = EmotionGenerator.generate_from_context(
        f"Initial mood: {mood}, Personality: {personality}",
        {"description": personality}
    )
    
    return {
        "location": location,
        "mood": mood,
        "emotion": emotion.to_dict()
    }

def _infer_locations_from_env(env_spec: Dict[str, Any]) -> List[str]:
    txt = (env_spec.get("prompt") or "") + " " + " ".join(env_spec.get("rules") or [])
    candidates = [w for w in [
        "Classroom","Hallway","Cafeteria","Gym","Playground","Dorm","Administration building","School gate",
        "Auditorium","Library","Stairwell","Lobby","Registration desk","Pharmacy","ER","Imaging","Lab",
        "Concourse","Security checkpoint","Platform","Inside train"
    ] if w.lower() in txt.lower()]
    if not candidates:
        candidates = ["Classroom","Hallway","Cafeteria","Library","Gym","Auditorium","School gate","Courtyard"]
    # de-dup & trim
    seen, out = set(), []
    for c in candidates:
        if c not in seen:
            out.append(c); seen.add(c)
    return out[:12]

def _rebalance_and_fix(personas: List[Dict[str, Any]], count: int, constraints: Dict[str, Any], env_title: str) -> List[Dict[str, Any]]:
    if not personas:
        # last resort
        return _bootstrap_personas(count, constraints, {"title": env_title, "prompt": "", "rules": []})

    gender_ratio = constraints.get("gender_ratio") or {"Male": 0.49, "Female": 0.49, "Non-binary/Other": 0.02}
    role_mix = constraints.get("role_mix") or {}
    locations = constraints.get("locations") or []

    # Unique English names
    names_seen = set()
    for p in personas:
        name = p.get("name") or ""
        if (not name) or (name in names_seen) or (" " not in name):
            p["name"] = _sample_en_name(p.get("gender"))
        names_seen.add(p["name"])

    # Gender re-balance (approx)
    target_counts = {g: int(round(r * count)) for g, r in gender_ratio.items()}
    diff = count - sum(target_counts.values())
    if diff != 0:
        keys = sorted(gender_ratio, key=gender_ratio.get, reverse=diff > 0)
        for k in keys:
            if diff == 0: break
            target_counts[k] += 1 if diff > 0 else -1
            diff += -1 if diff > 0 else 1

    def current_gender_hist():
        h: Dict[str, int] = {}
        for p in personas: h[p["gender"]] = h.get(p["gender"], 0) + 1
        return h

    hist = current_gender_hist()
    if hist:
        for g, tgt in target_counts.items():
            cur = hist.get(g, 0)
            if cur < tgt:
                over_g = max(hist, key=lambda x: hist.get(x, 0))
                need = tgt - cur
                idxs = [i for i, p in enumerate(personas) if p["gender"] == over_g][:need]
                for i in idxs:
                    personas[i]["gender"] = g
                    personas[i]["name"] = _sample_en_name(g)
                hist = current_gender_hist()

    # Role balancing if provided
    if role_mix:
        tgt_role_counts = {r: int(round(v * count)) for r, v in role_mix.items()}
        diff = count - sum(tgt_role_counts.values())
        if diff != 0:
            keys = sorted(role_mix, key=role_mix.get, reverse=diff > 0)
            for k in keys:
                if diff == 0: break
                tgt_role_counts[k] += 1 if diff > 0 else -1
                diff += -1 if diff > 0 else 1
        cur_role: Dict[str, int] = {}
        for p in personas:
            cur_role[p["occupation"]] = cur_role.get(p["occupation"], 0) + 1
        def indices_of(role): return [i for i, p in enumerate(personas) if p["occupation"] == role]
        over = [(r, cur_role.get(r, 0) - tgt) for r, tgt in tgt_role_counts.items() if cur_role.get(r, 0) > tgt]
        under = [(r, tgt_role_counts[r] - cur_role.get(r, 0)) for r in tgt_role_counts if cur_role.get(r, 0) < tgt_role_counts[r]]
        over.sort(key=lambda x: x[1], reverse=True)
        under.sort(key=lambda x: x[1], reverse=True)
        for r_over, extra in over:
            if extra <= 0: continue
            sel = indices_of(r_over)[:extra]
            for r_under, need in list(under):
                while need > 0 and sel:
                    idx = sel.pop()
                    personas[idx]["occupation"] = r_under
                    need -= 1
                under = [(r, n) for r, n in under if n > 0]

    # Locations fallback
    if locations:
        for p in personas:
            if p["initial_state"].get("location", "Start") not in locations:
                p["initial_state"]["location"] = random.choice(locations)

    return personas
