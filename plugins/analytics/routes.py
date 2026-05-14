"""
Plugin Analytics — KPIs et reporting B2B Prospector
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional
import logging

from core.database import get_db
from core.auth import get_current_active_user
from models.database.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/kpis")
async def get_kpis(
    period: str = Query("30d", description="7d, 30d, 90d, all"),
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retourne les KPIs principaux de la base prospects"""
    try:
        # Compute date filter
        now = datetime.utcnow()
        if period == "7d":
            since = now - timedelta(days=7)
        elif period == "30d":
            since = now - timedelta(days=30)
        elif period == "90d":
            since = now - timedelta(days=90)
        else:
            since = None

        # Total prospects
        total = db.execute(text("SELECT COUNT(*) FROM prospects")).scalar() or 0

        # Prospects this month
        this_month = db.execute(text(
            "SELECT COUNT(*) FROM prospects WHERE created_at >= :since"
        ), {"since": since or (now - timedelta(days=30))}).scalar() or 0

        # With email / phone
        with_email = db.execute(text(
            "SELECT COUNT(*) FROM prospects WHERE email IS NOT NULL AND email != ''"
        )).scalar() or 0

        with_phone = db.execute(text(
            "SELECT COUNT(*) FROM prospects WHERE phone IS NOT NULL AND phone != ''"
        )).scalar() or 0

        # Average score
        avg_score_row = db.execute(text(
            "SELECT AVG(score) FROM prospects WHERE score IS NOT NULL"
        )).scalar()
        avg_score = round(float(avg_score_row)) if avg_score_row else 0

        # Pipeline distribution
        pipeline_rows = db.execute(text("""
            SELECT COALESCE(pipeline_stage, 'Nouveau') as stage, COUNT(*) as cnt
            FROM prospects
            GROUP BY pipeline_stage
        """)).fetchall()
        pipeline_value = {row[0]: row[1] for row in pipeline_rows}

        # Score distribution
        score_dist = []
        for label, low, high in [("0-24", 0, 24), ("25-49", 25, 49), ("50-74", 50, 74), ("75-100", 75, 100)]:
            cnt = db.execute(text(
                "SELECT COUNT(*) FROM prospects WHERE score >= :low AND score <= :high"
            ), {"low": low, "high": high}).scalar() or 0
            score_dist.append({"range": label, "count": cnt})

        # Top regions
        region_rows = db.execute(text("""
            SELECT region, COUNT(*) as cnt FROM prospects
            WHERE region IS NOT NULL
            GROUP BY region ORDER BY cnt DESC LIMIT 8
        """)).fetchall()
        top_regions = [{"region": r[0], "count": r[1]} for r in region_rows]

        # Top NAF
        naf_rows = db.execute(text("""
            SELECT naf_label, COUNT(*) as cnt FROM prospects
            WHERE naf_label IS NOT NULL
            GROUP BY naf_label ORDER BY cnt DESC LIMIT 8
        """)).fetchall()
        top_naf = [{"naf_label": r[0], "count": r[1]} for r in naf_rows]

        # Daily additions (last 30 days)
        daily_rows = db.execute(text("""
            SELECT DATE(created_at) as day, COUNT(*) as cnt
            FROM prospects
            WHERE created_at >= :since
            GROUP BY DATE(created_at)
            ORDER BY day
        """), {"since": now - timedelta(days=30)}).fetchall()
        daily_additions = [{"date": str(r[0]), "count": r[1]} for r in daily_rows]

        # Source breakdown (from sources jsonb array if available, else fallback)
        try:
            src_rows = db.execute(text("""
                SELECT src, COUNT(*) as cnt
                FROM (
                    SELECT jsonb_array_elements_text(sources::jsonb) as src
                    FROM prospects WHERE sources IS NOT NULL AND sources != 'null'
                ) sub
                GROUP BY src ORDER BY cnt DESC LIMIT 8
            """)).fetchall()
            source_breakdown = [{"source": r[0], "count": r[1]} for r in src_rows]
        except Exception:
            source_breakdown = []

        # Enrichment rate (prospects with enrichment_data)
        enriched = db.execute(text(
            "SELECT COUNT(*) FROM prospects WHERE enrichment_data IS NOT NULL AND enrichment_data != '{}'"
        )).scalar() or 0
        enrichment_rate = round(enriched / total * 100) if total > 0 else 0

        # Conversion rate (pipeline_stage in Gagné)
        won = db.execute(text(
            "SELECT COUNT(*) FROM prospects WHERE pipeline_stage = 'Gagné'"
        )).scalar() or 0
        conversion_rate = round(won / total * 100) if total > 0 else 0

        return {
            "total_prospects": total,
            "prospects_this_month": this_month,
            "prospects_with_email": with_email,
            "prospects_with_phone": with_phone,
            "avg_score": avg_score,
            "pipeline_value": pipeline_value,
            "score_distribution": score_dist,
            "top_regions": top_regions,
            "top_naf": top_naf,
            "daily_additions": daily_additions,
            "source_breakdown": source_breakdown,
            "enrichment_rate": enrichment_rate,
            "conversion_rate": conversion_rate,
        }

    except Exception as e:
        logger.error(f"Analytics KPIs error: {e}")
        # Return empty structure rather than 500
        return {
            "total_prospects": 0, "prospects_this_month": 0,
            "prospects_with_email": 0, "prospects_with_phone": 0,
            "avg_score": 0, "pipeline_value": {}, "score_distribution": [],
            "top_regions": [], "top_naf": [], "daily_additions": [],
            "source_breakdown": [], "enrichment_rate": 0, "conversion_rate": 0,
        }


@router.get("/export/csv")
async def export_analytics_csv(
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Export rapport analytics en CSV"""
    from fastapi.responses import StreamingResponse
    import csv, io

    rows = db.execute(text("""
        SELECT company_name, city, region, naf_code, naf_label,
               score, pipeline_stage, email, phone,
               created_at, updated_at
        FROM prospects ORDER BY score DESC LIMIT 10000
    """)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Entreprise","Ville","Région","Code NAF","Secteur","Score",
                     "Étape Pipeline","Email","Téléphone","Créé le","Mis à jour le"])
    for row in rows:
        writer.writerow([str(v) if v is not None else "" for v in row])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_export.csv"}
    )
