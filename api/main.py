from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncpg
import json
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from api.models import CountStats, LiveStats, PolygonConfig, StatsFilter, ApiResponse
from core.database import db_manager
from core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="People Counting API",
    description="API untuk sistem deteksi dan counting orang",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for dashboard
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting People Counting API...")

@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.close()
    logger.info("API shutdown complete")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve dashboard HTML"""
    try:
        with open("dashboard/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Dashboard not found</h1><p>Please setup dashboard files</p>")

@app.get("/api/stats/", response_model=List[CountStats])
async def get_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD HH:MM:SS)"),
    area_id: Optional[int] = Query(None, description="Area ID filter"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=1000, description="Items per page")
):
    """Get historical count statistics with optional filters"""
    try:
        async with db_manager.get_async_session() as session:
            # Build query
            query = """
                SELECT 
                    c.area_id,
                    c.timestamp,
                    c.count_in,
                    c.count_out,
                    SUM(c.count_in) OVER (PARTITION BY c.area_id ORDER BY c.timestamp) as total_in,
                    SUM(c.count_out) OVER (PARTITION BY c.area_id ORDER BY c.timestamp) as total_out
                FROM counts c
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND c.timestamp >= $" + str(len(params) + 1)
                params.append(datetime.fromisoformat(start_date))
            
            if end_date:
                query += " AND c.timestamp <= $" + str(len(params) + 1)
                params.append(datetime.fromisoformat(end_date))
            
            if area_id:
                query += " AND c.area_id = $" + str(len(params) + 1)
                params.append(area_id)
            
            query += " ORDER BY c.timestamp DESC"
            query += f" LIMIT {limit} OFFSET {(page - 1) * limit}"
            
            # Execute using raw connection for now (simplified)
            conn = await asyncpg.connect(settings.database_url.replace("postgresql://", "postgresql://"))
            rows = await conn.fetch(query, *params)
            await conn.close()
            
            results = []
            for row in rows:
                results.append(CountStats(
                    area_id=row['area_id'],
                    timestamp=row['timestamp'],
                    count_in=row['count_in'],
                    count_out=row['count_out'],
                    total_in=row['total_in'],
                    total_out=row['total_out']
                ))
            
            return results
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats/live", response_model=LiveStats)
async def get_live_stats(area_id: Optional[int] = Query(1, description="Area ID")):
    """Get live/latest count statistics"""
    try:
        conn = await asyncpg.connect(settings.database_url.replace("postgresql://", "postgresql://"))
        
        # Get latest counts
        latest_count = await conn.fetchrow("""
            SELECT count_in, count_out, timestamp
            FROM counts 
            WHERE area_id = $1 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, area_id)
        
        # Get active objects (detected in last 30 seconds)
        active_objects = await conn.fetchval("""
            SELECT COUNT(DISTINCT object_id) 
            FROM detections 
            WHERE area_id = $1 
            AND timestamp > NOW() - INTERVAL '30 seconds'
        """, area_id)
        
        await conn.close()
        
        if latest_count:
            return LiveStats(
                area_id=area_id,
                current_count_in=latest_count['count_in'],
                current_count_out=latest_count['count_out'],
                last_detection=latest_count['timestamp'],
                active_objects=active_objects or 0
            )
        else:
            return LiveStats(
                area_id=area_id,
                current_count_in=0,
                current_count_out=0,
                last_detection=None,
                active_objects=0
            )
            
    except Exception as e:
        logger.error(f"Error getting live stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/area", response_model=ApiResponse)
async def update_area_config(config: PolygonConfig):
    """Update polygon area configuration"""
    try:
        # Save to JSON file
        config_data = {
            "name": config.name,
            "coordinates": config.coordinates
        }
        
        with open(settings.polygon_config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Update database
        conn = await asyncpg.connect(settings.database_url.replace("postgresql://", "postgresql://"))
        
        # Convert coordinates to PostgreSQL polygon format
        coords_str = ','.join([f"{x} {y}" for x, y in config.coordinates])
        geom_text = f"POLYGON(({coords_str},{config.coordinates[0][0]} {config.coordinates[0][1]}))"
        
        await conn.execute("""
            UPDATE areas 
            SET name = $1, geom = ST_GeomFromText($2, 0), updated_at = NOW()
            WHERE id = 1
        """, config.name, geom_text)
        
        await conn.close()
        
        return ApiResponse(
            success=True,
            message="Area configuration updated successfully",
            data={"config": config_data}
        )
        
    except Exception as e:
        logger.error(f"Error updating area config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
