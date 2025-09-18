# Multi-Agent Social Simulation Platform

This project is a **multi-agent simulation framework** powered by LLMs (e.g., DeepSeek-Chat).  
It enables researchers to design **social experiments in silico**, where agents with realistic personas interact within shared environments.  
Inspired by controversial experiments such as *The Third Wave*, this platform provides a **safe and ethical alternative** for studying collective behavior, authority, conformity, and social dynamics.

---

## ✨ Features

- **Experiment Management**
  - Create isolated experiment directories with environment specs, agents, relations, and logs.
  - Each experiment has its own `agents.json`, `env.json`, `relations.json`, and log files.

- **Persona Generation**
  - Agents have realistic **English names** (first + last).
  - Personas include gender, age, occupation, education, income, description, initial memory & state.
  - Supports **LLM-based generation** with fallback **local synthesis** to ensure diversity.
  - Demographic and occupational distribution can be guided by constraints or inferred from environment.

- **Environment Modeling**
  - Environments are expanded from a simple `--env-hint` into a detailed `env.json`:
    - Title
    - Prompt (detailed description)
    - Rules (explicit constraints)
  - Example: “1960s American high school classroom” → generates classroom, cafeteria, gym, etc.

- **Relation Graph**
  - Each experiment includes a **social relation network** (`relations.json`).
  - Relations (family, coworker, neighbor, acquaintance) influence interaction probability and trust.
  - Strength factor (`0–1`) controls frequency and reliability of interactions.

- **Simulation Loop**
  - Tick-based simulation (`app_loop`) advances time automatically (default: every 60s).
  - Agents update action, speech, state, thoughts, and memory each tick.
  - Group encounters at the same location are simulated with **hard constraints** from relations.
  - Logs are saved both per-agent and as collective events.

- **Logging & Analysis**
  - `logs/agents/<agent>.jsonl` → each agent’s step-by-step log.
  - `logs/events/encounters.jsonl` → all group events per tick.
  - JSONL format enables downstream **quantitative analysis** and **visualization**.

---

## 📦 Installation

```bash
# clone repo
git clone <this-repo>
cd agentsociety_backend

# create environment (example: conda)
conda create -n agentsociety python=3.11
conda activate agentsociety

# install dependencies
pip install -r requirements.txt
