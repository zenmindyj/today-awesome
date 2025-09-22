import os
import sys
from fastapi import FastAPI, HTTPException, APIRouter, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

# --- 修复相对路径问题 ---
# 将项目根目录添加到系统路径中，以便能正确找到 database 和 ai_service 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Database
from backend.ai_service import AIService

app = FastAPI(title="今天好棒啊", description="记录每天的好棒时刻")

# --- 路径配置 (专为本地运行和打包设计) ---
# 无论脚本从哪里运行，都能正确找到文件
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)


# --- 数据库和服务初始化 (使用正确的本地路径) ---
db_demo = Database(db_path=os.path.join(DATA_DIR, "demo.db"))
db_user = Database(db_path=os.path.join(DATA_DIR, "user.db"))
ai_service = AIService()

# --- 挂载静态文件和模板 ---
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
templates = Jinja2Templates(directory=FRONTEND_DIR)


@app.on_event("startup")
def startup_event():
    db_user.init_database()
    db_demo.init_database()
    db_demo.seed_database_if_empty()


# --- Pydantic 模型 ---
class EntryRequest(BaseModel):
    content: str
    entry_date: Optional[str] = None

class SummaryRequest(BaseModel):
    start_date: str
    end_date: str

class QueryRequest(BaseModel):
    question: str


# --- API Routers ---
user_router = APIRouter(prefix="/api/user")
demo_router = APIRouter(prefix="/api/demo")


# --- 用户数据 API (/api/user) ---

@user_router.post("/entries")
async def add_user_entry(entry: EntryRequest):
    try:
        category = await ai_service.auto_categorize(entry.content)
        db_user.add_entry(entry.content, category, entry.entry_date)
        return {"message": "条目添加成功", "content": entry.content, "category": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/entries")
async def get_user_entries(page: int = 1, per_page: int = 25):
    try:
        offset = (page - 1) * per_page
        total_count = db_user.get_entries_count()
        entries = db_user.get_entries_paginated(offset, per_page)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        return {
            "entries": entries,
            "pagination": {
                "current_page": page, "per_page": per_page,
                "total_count": total_count, "total_pages": total_pages,
                "has_next": page < total_pages, "has_prev": page > 1
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.delete("/entries/{entry_id}")
async def delete_user_entry(entry_id: str):
    try:
        success = db_user.delete_entry(entry_id)
        if success:
            return {"message": "记录删除成功"}
        else:
            raise HTTPException(status_code=404, detail="记录不存在或删除失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.post("/summary")
async def get_user_summary(request: SummaryRequest):
    try:
        # Step 1: Get precise statistics from the database
        statistics = db_user.get_statistics_by_date_range(request.start_date, request.end_date)
        
        # Step 2: Handle case where there's no data
        if not statistics:
            time_range_name = f"{request.start_date} 至 {request.end_date}"
            return {"summary": f"在 {time_range_name} 期间您还没有记录任何好棒的时刻。"}

        # Step 3: Pass the accurate statistics to the AI for analysis
        summary_text = await ai_service.generate_weekly_summary(statistics)
        
        return {
            "summary": summary_text, 
            "entries_count": statistics['total_entries'], 
            "time_range": f"{statistics['start_date']} 至 {statistics['end_date']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/summary-options")
async def get_user_summary_options():
    try:
        return {
            "week_options": db_user.get_last_n_weeks_ranges(3),
            "month_options": db_user.get_data_containing_months_ranges()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取总结选项失败：{str(e)}")

@user_router.post("/smart-query")
async def smart_user_query(query: QueryRequest):
    try:
        entries = db_user.get_entries(limit=1000)
        if not entries:
            return {"answer": "您还没有任何记录，快去添加吧！", "relevant_entries": []}
        answers = await ai_service.answer_smart_query(query.question, entries)
        return answers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@user_router.post("/import-text")
async def import_user_text(request: dict):
    entries_data = request.get('entries', [])
    if not entries_data:
        raise HTTPException(status_code=400, detail="没有提供要导入的记录")
    
    success_count = 0
    errors = []
    for item in entries_data:
        try:
            content = item.get('content', '').strip()
            if content:
                category = await ai_service.auto_categorize(content)
                db_user.add_entry(content, category, item.get('entry_date'))
                success_count += 1
        except Exception as e:
            errors.append(f"导入 '{content[:20]}...' 失败: {e}")
            
    return {
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors
    }
    
@user_router.post("/reset-database")
async def reset_user_database():
    try:
        db_user.delete_all_entries()
        return {"message": "您的个人数据已清空，可以开始重新记录了。"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置数据库失败: {e}")


# --- 演示数据 API (/api/demo) - 只读 ---

@demo_router.get("/entries")
async def get_demo_entries(page: int = 1, per_page: int = 25):
    try:
        offset = (page - 1) * per_page
        total_count = db_demo.get_entries_count()
        entries = db_demo.get_entries_paginated(offset, per_page)
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
        return {
            "entries": entries,
            "pagination": {
                "current_page": page, "per_page": per_page,
                "total_count": total_count, "total_pages": total_pages,
                "has_next": page < total_pages, "has_prev": page > 1
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@demo_router.post("/summary")
async def get_demo_summary(request: SummaryRequest):
    try:
        # Step 1: Get precise statistics from the database
        statistics = db_demo.get_statistics_by_date_range(request.start_date, request.end_date)
        
        # Step 2: Handle case where there's no data
        if not statistics:
            time_range_name = f"{request.start_date} 至 {request.end_date}"
            return {"summary": f"在 {time_range_name} 期间没有演示数据。"}

        # Step 3: Pass the accurate statistics to the AI for analysis
        summary_text = await ai_service.generate_weekly_summary(statistics)

        return {
            "summary": summary_text, 
            "entries_count": statistics['total_entries'], 
            "time_range": f"{statistics['start_date']} 至 {statistics['end_date']}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@demo_router.get("/summary-options")
async def get_demo_summary_options():
    try:
        return {
            "week_options": db_demo.get_last_n_weeks_ranges(3),
            "month_options": db_demo.get_data_containing_months_ranges()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取总结选项失败：{str(e)}")

@demo_router.post("/smart-query")
async def smart_demo_query(query: QueryRequest):
    try:
        entries = db_demo.get_entries(limit=1000)
        answers = await ai_service.answer_smart_query(query.question, entries)
        return answers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@demo_router.delete("/entries/{entry_id}")
async def delete_demo_entry(entry_id: str):
    try:
        success = db_demo.delete_entry(entry_id)
        if success:
            return {"message": "记录删除成功"}
        else:
            raise HTTPException(status_code=404, detail="记录不存在或删除失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 注册 Routers ---
app.include_router(user_router)
app.include_router(demo_router)


# --- 前端页面路由 (恢复) ---
@app.get("/", response_class=HTMLResponse)
async def read_user_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "page_mode": "user"})

@app.get("/demo", response_class=HTMLResponse)
async def read_demo_page(request: Request):
    return templates.TemplateResponse("demo.html", {"request": request, "page_mode": "demo"})


# --- 本地运行 ---
if __name__ == "__main__":
    import uvicorn
    # 监听 0.0.0.0 可以让同局域网设备访问，更灵活
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
