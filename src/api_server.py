"""
AgentSociety Backend API Server
提供Web UI所需的所有API接口
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.experiments.manager import create_experiment
from src.agentsim.models import AgentPersona, EnvSpec, SimulationConfig, AgentTickOutput
from src.agentsim.simulator import run_tick_with_interactions
from src.agentsim.logger import set_exp_log_roots, append_agent_log
from src.agentsim.registry import set_agents_path

load_dotenv()

app = FastAPI(title="AgentSociety API", version="1.0.0")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储运行中的模拟
running_simulations: Dict[str, Dict[str, Any]] = {}

# ==================== API Models ====================

class CreateExperimentRequest(BaseModel):
    name: str
    env_hint: str
    count: int
    relation_influence: float = 0.8
    constraints_json: Optional[str] = None

class StartSimulationRequest(BaseModel):
    temperature: float = 0.7
    max_tokens: int = 700
    interval: float = 10.0  # 默认10秒一个tick，比60秒快些用于演示
    max_ticks: Optional[int] = None

class ExperimentInfo(BaseModel):
    name: str
    slug: str
    path: str
    created_at: str
    agent_count: int
    has_logs: bool

# ==================== API Routes ====================

@app.get("/")
async def root():
    """返回API基本信息"""
    return {
        "name": "AgentSociety API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/api/experiments", response_model=List[ExperimentInfo])
async def list_experiments():
    """获取所有实验列表"""
    experiments_dir = "experiments"
    if not os.path.exists(experiments_dir):
        return []
    
    experiments = []
    for exp_name in os.listdir(experiments_dir):
        exp_path = os.path.join(experiments_dir, exp_name)
        if not os.path.isdir(exp_path):
            continue
        
        meta_path = os.path.join(exp_path, "meta.json")
        if not os.path.exists(meta_path):
            continue
        
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            
            agents_path = os.path.join(exp_path, "agents.json")
            agent_count = 0
            if os.path.exists(agents_path):
                with open(agents_path, "r", encoding="utf-8") as f:
                    agents = json.load(f)
                    agent_count = len(agents) if isinstance(agents, list) else 0
            
            logs_dir = os.path.join(exp_path, "logs")
            has_logs = os.path.exists(logs_dir) and len(os.listdir(logs_dir)) > 0
            
            # 获取创建时间（从目录修改时间）
            created_at = datetime.fromtimestamp(os.path.getctime(exp_path)).isoformat()
            
            experiments.append(ExperimentInfo(
                name=meta.get("name", exp_name),
                slug=meta.get("slug", exp_name),
                path=exp_path,
                created_at=created_at,
                agent_count=agent_count,
                has_logs=has_logs
            ))
        except Exception as e:
            print(f"Error loading experiment {exp_name}: {e}")
            continue
    
    # 按创建时间倒序排列
    experiments.sort(key=lambda x: x.created_at, reverse=True)
    return experiments

@app.post("/api/experiments")
async def create_new_experiment(req: CreateExperimentRequest, background_tasks: BackgroundTasks):
    """创建新实验"""
    try:
        constraints = None
        if req.constraints_json:
            try:
                constraints = json.loads(req.constraints_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid constraints JSON")
        
        exp_dir = await create_experiment(
            root_dir="experiments",
            name=req.name,
            env_hint=req.env_hint,
            count=req.count,
            relation_influence=req.relation_influence,
            constraints=constraints
        )
        
        return {
            "success": True,
            "message": "实验创建成功",
            "experiment_path": exp_dir
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建实验失败: {str(e)}")

@app.get("/api/experiments/{exp_slug}")
async def get_experiment_detail(exp_slug: str):
    """获取实验详细信息"""
    exp_path = os.path.join("experiments", exp_slug)
    if not os.path.exists(exp_path):
        raise HTTPException(status_code=404, detail="实验不存在")
    
    try:
        # 读取所有实验文件
        result = {}
        
        # Meta信息
        meta_path = os.path.join(exp_path, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                result["meta"] = json.load(f)
        
        # 环境信息
        env_path = os.path.join(exp_path, "env.json")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                result["environment"] = json.load(f)
        
        # Agents信息
        agents_path = os.path.join(exp_path, "agents.json")
        if os.path.exists(agents_path):
            with open(agents_path, "r", encoding="utf-8") as f:
                result["agents"] = json.load(f)
        
        # 约束信息
        constraints_path = os.path.join(exp_path, "constraints.json")
        if os.path.exists(constraints_path):
            with open(constraints_path, "r", encoding="utf-8") as f:
                result["constraints"] = json.load(f)
        
        # 关系图
        relations_path = os.path.join(exp_path, "relations.json")
        if os.path.exists(relations_path):
            with open(relations_path, "r", encoding="utf-8") as f:
                result["relations"] = json.load(f)
        
        # 检查模拟状态
        result["simulation_running"] = exp_slug in running_simulations
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取实验数据失败: {str(e)}")

@app.get("/api/experiments/{exp_slug}/logs")
async def get_experiment_logs(exp_slug: str, agent_name: Optional[str] = None, limit: int = 100):
    """获取实验日志"""
    exp_path = os.path.join("experiments", exp_slug)
    logs_dir = os.path.join(exp_path, "logs", "agents")
    
    if not os.path.exists(logs_dir):
        return {"logs": []}
    
    try:
        if agent_name:
            # 获取特定agent的日志
            log_file = os.path.join(logs_dir, f"{agent_name}.jsonl")
            if not os.path.exists(log_file):
                return {"logs": []}
            
            logs = []
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
            
            # 限制返回数量
            return {"logs": logs[-limit:] if len(logs) > limit else logs}
        else:
            # 获取所有agent的最新日志
            all_logs = []
            for log_file in os.listdir(logs_dir):
                if log_file.endswith(".jsonl"):
                    file_path = os.path.join(logs_dir, log_file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        if lines:
                            # 只取最后一条
                            last_line = lines[-1].strip()
                            if last_line:
                                log_entry = json.loads(last_line)
                                log_entry["agent_file"] = log_file
                                all_logs.append(log_entry)
            
            return {"logs": all_logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")

@app.post("/api/experiments/{exp_slug}/start")
async def start_simulation(exp_slug: str, req: StartSimulationRequest, background_tasks: BackgroundTasks):
    """启动模拟"""
    if exp_slug in running_simulations:
        raise HTTPException(status_code=400, detail="该实验的模拟已在运行中")
    
    exp_path = os.path.join("experiments", exp_slug)
    if not os.path.exists(exp_path):
        raise HTTPException(status_code=404, detail="实验不存在")
    
    # 在后台启动模拟（显式调度异步任务）
    asyncio.create_task(
        run_simulation_background(
            exp_slug,
            exp_path,
            req.temperature,
            req.max_tokens,
            req.interval,
            req.max_ticks,
        )
    )
    
    return {
        "success": True,
        "message": "模拟已启动"
    }

@app.post("/api/experiments/{exp_slug}/stop")
async def stop_simulation(exp_slug: str):
    """停止模拟"""
    if exp_slug not in running_simulations:
        raise HTTPException(status_code=400, detail="该实验没有运行中的模拟")
    
    running_simulations[exp_slug]["stop_flag"] = True
    return {
        "success": True,
        "message": "正在停止模拟..."
    }

@app.get("/api/experiments/{exp_slug}/status")
async def get_simulation_status(exp_slug: str):
    """获取模拟状态"""
    if exp_slug not in running_simulations:
        return {
            "running": False,
            "current_tick": 0,
            "message": "模拟未运行"
        }
    
    sim = running_simulations[exp_slug]
    return {
        "running": not sim.get("stop_flag", False),
        "current_tick": sim.get("current_tick", 0),
        "message": sim.get("message", "运行中")
    }

@app.delete("/api/experiments/{exp_slug}")
async def delete_experiment(exp_slug: str):
    """删除实验"""
    exp_path = os.path.join("experiments", exp_slug)
    if not os.path.exists(exp_path):
        raise HTTPException(status_code=404, detail="实验不存在")
    
    # 如果正在运行，先停止
    if exp_slug in running_simulations:
        running_simulations[exp_slug]["stop_flag"] = True
        await asyncio.sleep(1)  # 等待一秒让模拟停止
    
    try:
        import shutil
        shutil.rmtree(exp_path)
        return {
            "success": True,
            "message": "实验已删除"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# ==================== Background Tasks ====================

async def run_simulation_background(
    exp_slug: str,
    exp_path: str,
    temperature: float,
    max_tokens: int,
    interval: float,
    max_ticks: Optional[int]
):
    """后台运行模拟"""
    try:
        # 加载实验数据
        with open(os.path.join(exp_path, "env.json"), "r", encoding="utf-8") as f:
            env_obj = json.load(f)
        with open(os.path.join(exp_path, "agents.json"), "r", encoding="utf-8") as f:
            agents_raw = json.load(f)
        with open(os.path.join(exp_path, "meta.json"), "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        # 设置日志路径
        set_agents_path(os.path.join(exp_path, "agents.json"))
        set_exp_log_roots(os.path.join(exp_path, "logs"))
        
        # 创建agents和环境
        agents = [AgentPersona(**a) for a in agents_raw]
        env_spec = EnvSpec(**env_obj)
        
        relation_influence = meta.get("relation_influence", 0.8)
        config = SimulationConfig(
            steps=1,
            temperature=temperature,
            max_tokens=max_tokens,
            visibility="local",
            relation_influence=relation_influence
        )
        
        # 初始化模拟状态
        running_simulations[exp_slug] = {
            "current_tick": 0,
            "stop_flag": False,
            "message": "初始化中..."
        }
        
        # 记录元信息
        for a in agents:
            append_agent_log(a.name, {
                "type": "sim_meta",
                "title": env_spec.title,
                "with_interactions": True,
                "interval_sec": interval,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "visibility": "local",
                "relation_influence": relation_influence,
            })
        
        history: Dict[str, List[AgentTickOutput]] = {a.id: [] for a in agents}
        tick = 0
        
        running_simulations[exp_slug]["message"] = "运行中"
        
        # 运行模拟循环
        while True:
            # 检查停止标志
            if running_simulations[exp_slug].get("stop_flag", False):
                running_simulations[exp_slug]["message"] = "已停止"
                break
            
            # 检查是否达到最大tick数
            if max_ticks is not None and tick >= max_ticks:
                running_simulations[exp_slug]["message"] = f"已完成{max_ticks}个tick"
                break
            
            try:
                # 运行一个tick
                results = await run_tick_with_interactions(agents, env_spec, config, tick, history)
                for out in results:
                    history[out.agent_id].append(out)
                
                running_simulations[exp_slug]["current_tick"] = tick
                tick += 1
                
                # 等待下一个tick
                await asyncio.sleep(interval)
            except Exception as e:
                running_simulations[exp_slug]["message"] = f"错误: {str(e)}"
                print(f"Simulation error in {exp_slug}: {e}")
                break
        
    except Exception as e:
        print(f"Failed to start simulation for {exp_slug}: {e}")
        if exp_slug in running_simulations:
            running_simulations[exp_slug]["message"] = f"启动失败: {str(e)}"
    finally:
        # 清理
        if exp_slug in running_simulations:
            await asyncio.sleep(5)  # 保持状态5秒供查询
            del running_simulations[exp_slug]

# ==================== Static Files ====================

# 挂载静态文件目录（放在最后，避免覆盖API路由）
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/ui")
@app.get("/ui/{full_path:path}")
async def serve_ui(full_path: str = ""):
    """提供前端UI"""
    ui_dir = "static"
    if full_path and full_path != "":
        file_path = os.path.join(ui_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
    
    # 默认返回index.html
    index_path = os.path.join(ui_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"message": "UI not found. Please create static/index.html"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("AgentSociety Web UI Server")
    print("=" * 60)
    print("访问 http://localhost:8000/ui 使用Web界面")
    print("访问 http://localhost:8000/docs 查看API文档")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)

