"""Plugin Analytics — KPIs et reporting B2B Prospector."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter()


@router.get("/kpis")
async def get_kpis(
    period: str = Query("30d"),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    try:
        now = datetime.now(timezone.utc)
        since = now - {"7d": timedelta(days=7), "30d": timedelta(days=30), "90d": timedelta(days=90)}.get(period, timedelta(days=30))

        total = (await db.execute(text("SELECT COUNT(*) FROM prospects"))).scalar() or 0
        this_month = (await db.execute(text("SELECT COUNT(*) FROM prospects WHERE created_at >= :s"), {"s": since})).scalar() or 0
        with_email = (await db.execute(text("SELECT COUNT(*) FROM prospects WHERE email IS NOT NULL AND email != ''"))).scalar() or 0
        with_phone = (await db.execute(text("SELECT COUNT(*) FROM prospects WHERE phone IS NOT NULL AND phone != ''"))).scalar() or 0

        avg_score_row = (await db.execute(text("SELECT AVG(propensity_score) FROM prospects WHERE propensity_score IS NOT NULL"))).scalar()
        avg_score = round(float(avg_score_row)) if avg_score_row else 0

        pipeline_rows = (await db.execute(text("""
            SELECT COALESCE(ps.name, 'Sans étape') as stage, COUNT(p.id) as cnt
            FROM prospects p
            LEFT JOIN pipeline_stages ps ON p.stage_id = ps.id
            GROUP BY ps.name ORDER BY cnt DESC
        """))).fetchall()
        pipeline_value = {r[0]: r[1] for r in pipeline_rows}

        score_dist = []
        for label, low, high in [("0-24", 0, 24), ("25-49", 25, 49), ("50-74", 50, 74), ("75-100", 75, 100)]:
            cnt = (await db.execute(text("SELECT COUNT(*) FROM prospects WHERE propensity_score >= :l AND propensity_score <= :h"), {"l": low, "h": high})).scalar() or 0
            score_dist.append({"range": label, "count": cnt})

        region_rows = (await db.execute(text("SELECT region, COUNT(*) as cnt FROM prospects WHERE region IS NOT NULL GROUP BY region ORDER BY cnt DESC LIMIT 8"))).fetchall()
        top_regions = [{"region": r[0], "count": r[1]} for r in region_rows]

        naf_rows = (await db.execute(text("SELECT naf_label, COUNT(*) as cnt FROM prospects WHERE naf_label IS NOT NULL GROUP BY naf_label ORDER BY cnt DESC LIMIT 8"))).fetchall()
        top_naf = [{"naf_label": r[0], "count": r[1]} for r in naf_rows]

        daily_rows = (await db.execute(text("SELECT DATE(created_at) as day, COUNT(*) as cnt FROM prospects WHERE created_at >= :s GROUP BY DATE(created_at) ORDER BY day"), {"s": since})).fetchall()
        daily_additions = [{"date": str(r[0]), "count": r[1]} for r in daily_rows]

        try:
            src_rows = (await db.execute(text("""
                SELECT src, COUNT(*) as cnt FROM (
                    SELECT jsonb_array_elements_text(sources_used::jsonb) as src
                    FROM prospects WHERE sources_used IS NOT NULL AND sources_used::text != '[]'
                ) sub GROUP BY src ORDER BY cnt DESC LIMIT 8
            """))).fetchall()
            source_breakdown = [{"source": r[0], "count": r[1]} for r in src_rows]
        except Exception:
            source_breakdown = []

        enriched = (await db.execute(text("SELECT COUNT(*) FROM prospects WHERE enrichment IS NOT NULL AND enrichment::text != '{}'"))).scalar() or 0
        won = (await db.execute(text("SELECT COUNT(*) FROM prospects p JOIN pipeline_stages ps ON p.stage_id = ps.id WHERE ps.is_won = true"))).scalar() or 0

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
            "enrichment_rate": round(enriched / total * 100) if total else 0,
            "conversion_rate": round(won / total * 100) if total else 0,
        }
    except Exception as e:
        return {
            "total_prospects": 0, "prospects_this_month": 0,
            "prospects_with_email": 0, "prospects_with_phone": 0,
            "avg_score": 0, "pipeline_value": {}, "score_distribution": [],
            "top_regions": [], "top_naf": [], "daily_additions": [],
            "source_breakdown": [], "enrichment_rate": 0, "conversion_rate": 0,
        }


@router.get("/export/csv")
async def export_analytics_csv(
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import StreamingResponse
    import csv, io

    rows = (await db.execute(text("""
        SELECT p.company_name, p.city, p.region, p.naf_code, p.naf_label,
               p.propensity_score, ps.name as stage, p.email, p.phone, p.created_at
        FROM prospects p
        LEFT JOIN pipeline_stages ps ON p.stage_id = ps.id
        ORDER BY p.propensity_score DESC NULLS LAST LIMIT 10000
    """))).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Entreprise","Ville","Région","Code NAF","Secteur","Score","Étape","Email","Téléphone","Créé le"])
    for row in rows:
        writer.writerow([str(v) if v is not None else "" for v in row])
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics_export.csv"},
    )
