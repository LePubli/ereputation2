"""
Plugin Themes — Système de thèmes WordPress-like.

Routes :
    GET    /api/v1/themes              → liste thèmes
    GET    /api/v1/themes/active       → thème actif (public, sans auth)
    POST   /api/v1/themes              → créer thème
    PATCH  /api/v1/themes/{id}         → modifier thème
    POST   /api/v1/themes/{id}/activate → activer thème
    DELETE /api/v1/themes/{id}         → supprimer (si non builtin)
    POST   /api/v1/themes/import       → importer JSON
    GET    /api/v1/themes/{id}/export  → exporter JSON
"""
import json
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import CurrentUser
from core.database import get_db

router = APIRouter(prefix="/api/v1/themes", tags=["themes"])


class ThemeCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    author: str = "Custom"
    preview_color: str = "#0d6efd"
    preview_bg: str = "#f2f6ff"
    css_variables: dict = {}
    layout: dict = {}


class ThemeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    preview_color: str | None = None
    preview_bg: str | None = None
    css_variables: dict | None = None
    layout: dict | None = None


# ── Thèmes builtin ──────────────────────────────────────────────────

BUILTIN_THEMES = [
    {
        "name": "CRMi Light",
        "slug": "crmi-light",
        "description": "Thème clair officiel CRMi — professionnel et épuré",
        "author": "B2B Prospector",
        "version": "1.0.0",
        "preview_color": "#0d6efd",
        "preview_bg": "#f2f6ff",
        "is_builtin": True,
        "is_active": True,
        "css_variables": {
            "--bg-primary": "#f2f6ff",
            "--bg-secondary": "#ffffff",
            "--bg-card": "#ffffff",
            "--bg-tertiary": "#f0f4ff",
            "--bg-sidebar": "#ffffff",
            "--bg-hover": "rgba(13,110,253,0.06)",
            "--border-color": "#e5e9f2",
            "--text-primary": "#212529",
            "--text-secondary": "#6c757d",
            "--text-muted": "#adb5bd",
            "--accent-blue": "#0d6efd",
            "--accent-green": "#198754",
            "--accent-red": "#dc3545",
            "--accent-orange": "#fd7e14",
            "--accent-purple": "#6f42c1",
            "--shadow-card": "0 1px 4px rgba(0,0,0,.08)",
            "--radius-lg": "10px",
        },
        "layout": {"sidebar_width": "240px", "header_height": "60px"},
    },
    {
        "name": "Dark Pro",
        "slug": "dark-pro",
        "description": "Thème sombre professionnel — idéal pour les longues sessions",
        "author": "B2B Prospector",
        "version": "1.0.0",
        "preview_color": "#6366f1",
        "preview_bg": "#0d1117",
        "is_builtin": True,
        "css_variables": {
            "--bg-primary": "#0d1117",
            "--bg-secondary": "#161b22",
            "--bg-card": "#1c2128",
            "--bg-tertiary": "#21262d",
            "--bg-sidebar": "#0d1117",
            "--bg-hover": "rgba(255,255,255,0.04)",
            "--border-color": "#30363d",
            "--text-primary": "#e6edf3",
            "--text-secondary": "#8b949e",
            "--text-muted": "#484f58",
            "--accent-blue": "#6366f1",
            "--accent-green": "#3fb950",
            "--accent-red": "#f85149",
            "--accent-orange": "#d29922",
            "--accent-purple": "#8b5cf6",
            "--shadow-card": "0 1px 4px rgba(0,0,0,.3)",
            "--radius-lg": "10px",
        },
        "layout": {"sidebar_width": "240px", "header_height": "60px"},
    },
    {
        "name": "Midnight Blue",
        "slug": "midnight-blue",
        "description": "Bleu nuit élégant avec accents dorés",
        "author": "B2B Prospector",
        "version": "1.0.0",
        "preview_color": "#f59e0b",
        "preview_bg": "#0f172a",
        "is_builtin": True,
        "css_variables": {
            "--bg-primary": "#0f172a",
            "--bg-secondary": "#1e293b",
            "--bg-card": "#1e293b",
            "--bg-tertiary": "#334155",
            "--bg-sidebar": "#0f172a",
            "--bg-hover": "rgba(245,158,11,0.08)",
            "--border-color": "#334155",
            "--text-primary": "#f1f5f9",
            "--text-secondary": "#94a3b8",
            "--text-muted": "#64748b",
            "--accent-blue": "#f59e0b",
            "--accent-green": "#10b981",
            "--accent-red": "#ef4444",
            "--accent-orange": "#f97316",
            "--accent-purple": "#8b5cf6",
            "--shadow-card": "0 1px 8px rgba(0,0,0,.4)",
            "--radius-lg": "10px",
        },
        "layout": {"sidebar_width": "240px", "header_height": "60px"},
    },
    {
        "name": "Forest Green",
        "slug": "forest-green",
        "description": "Vert naturel apaisant — zen et productif",
        "author": "B2B Prospector",
        "version": "1.0.0",
        "preview_color": "#16a34a",
        "preview_bg": "#f0fdf4",
        "is_builtin": True,
        "css_variables": {
            "--bg-primary": "#f0fdf4",
            "--bg-secondary": "#ffffff",
            "--bg-card": "#ffffff",
            "--bg-tertiary": "#dcfce7",
            "--bg-sidebar": "#ffffff",
            "--bg-hover": "rgba(22,163,74,0.06)",
            "--border-color": "#bbf7d0",
            "--text-primary": "#14532d",
            "--text-secondary": "#166534",
            "--text-muted": "#4ade80",
            "--accent-blue": "#16a34a",
            "--accent-green": "#15803d",
            "--accent-red": "#dc2626",
            "--accent-orange": "#d97706",
            "--accent-purple": "#7c3aed",
            "--shadow-card": "0 1px 4px rgba(22,163,74,.1)",
            "--radius-lg": "10px",
        },
        "layout": {"sidebar_width": "240px", "header_height": "60px"},
    },
]


# ── Routes ──────────────────────────────────────────────────────────

@router.get("/active")
async def get_active_theme(db: AsyncSession = Depends(get_db)):
    """Retourne le thème actif (public, appelé par ThemeProvider)."""
    from models.database.theme import Theme

    theme = (await db.execute(
        select(Theme).where(Theme.is_active.is_(True))
    )).scalar_one_or_none()

    if not theme:
        # Fallback CRMi Light
        bt = next(t for t in BUILTIN_THEMES if t["slug"] == "crmi-light")
        return {"css_variables": bt["css_variables"], "layout": bt.get("layout", {}), "name": bt["name"]}

    return {
        "id": str(theme.id),
        "name": theme.name,
        "css_variables": theme.css_variables,
        "layout": theme.layout,
    }


@router.get("")
async def list_themes(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les thèmes disponibles."""
    from models.database.theme import Theme

    await _ensure_builtins(db)

    themes = (await db.execute(select(Theme).order_by(Theme.is_builtin.desc(), Theme.name))).scalars().all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "slug": t.slug,
            "description": t.description,
            "author": t.author,
            "version": t.version,
            "preview_color": t.preview_color,
            "preview_bg": t.preview_bg,
            "is_active": t.is_active,
            "is_builtin": t.is_builtin,
            "variables_count": len(t.css_variables),
        }
        for t in themes
    ]


@router.post("/{theme_id}/activate")
async def activate_theme(
    theme_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Active un thème — désactive tous les autres. Instantané."""
    from models.database.theme import Theme

    theme = (await db.execute(select(Theme).where(Theme.id == theme_id))).scalar_one_or_none()
    if not theme:
        raise HTTPException(404, "Thème introuvable")

    # Désactive tous
    await db.execute(update(Theme).values(is_active=False))
    # Active celui-ci
    theme.is_active = True
    await db.commit()

    return {
        "message": f"Thème '{theme.name}' activé",
        "theme": theme.name,
        "css_variables": theme.css_variables,
        "layout": theme.layout,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_theme(
    body: ThemeCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Crée un nouveau thème personnalisé."""
    from models.database.theme import Theme

    existing = (await db.execute(select(Theme).where(Theme.slug == body.slug))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, f"Slug '{body.slug}' déjà utilisé")

    theme = Theme(
        name=body.name,
        slug=body.slug,
        description=body.description,
        author=body.author,
        preview_color=body.preview_color,
        preview_bg=body.preview_bg,
        css_variables=body.css_variables,
        layout=body.layout,
        is_builtin=False,
    )
    db.add(theme)
    await db.commit()
    await db.refresh(theme)

    return {"id": str(theme.id), "name": theme.name, "slug": theme.slug}


@router.patch("/{theme_id}")
async def update_theme(
    theme_id: UUID,
    body: ThemeUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Modifie un thème (builtin ou custom)."""
    from models.database.theme import Theme

    theme = (await db.execute(select(Theme).where(Theme.id == theme_id))).scalar_one_or_none()
    if not theme:
        raise HTTPException(404, "Thème introuvable")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(theme, field, value)

    await db.commit()
    await db.refresh(theme)

    return {"id": str(theme.id), "name": theme.name, "is_active": theme.is_active}


@router.delete("/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Supprime un thème (uniquement les thèmes non-builtin)."""
    from models.database.theme import Theme

    theme = (await db.execute(select(Theme).where(Theme.id == theme_id))).scalar_one_or_none()
    if not theme:
        raise HTTPException(404, "Thème introuvable")
    if theme.is_builtin:
        raise HTTPException(400, "Les thèmes builtin ne peuvent pas être supprimés")
    if theme.is_active:
        raise HTTPException(400, "Impossible de supprimer le thème actif")

    await db.delete(theme)
    await db.commit()


@router.post("/import")
async def import_theme(
    body: dict,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Importe un thème depuis un JSON."""
    from models.database.theme import Theme

    required = {"name", "slug", "css_variables"}
    if not required.issubset(body.keys()):
        raise HTTPException(400, f"Champs requis: {required}")

    existing = (await db.execute(select(Theme).where(Theme.slug == body["slug"]))).scalar_one_or_none()
    if existing:
        body["slug"] = f"{body['slug']}-{uuid4().hex[:6]}"

    theme = Theme(
        name=body["name"],
        slug=body["slug"],
        description=body.get("description"),
        author=body.get("author", "Importé"),
        version=body.get("version", "1.0.0"),
        preview_color=body.get("preview_color", "#0d6efd"),
        preview_bg=body.get("preview_bg", "#f2f6ff"),
        css_variables=body["css_variables"],
        layout=body.get("layout", {}),
        is_builtin=False,
    )
    db.add(theme)
    await db.commit()
    await db.refresh(theme)

    return {"id": str(theme.id), "name": theme.name, "message": "Thème importé avec succès"}


@router.get("/{theme_id}/export")
async def export_theme(
    theme_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Exporte un thème en JSON téléchargeable."""
    from models.database.theme import Theme
    from fastapi.responses import Response

    theme = (await db.execute(select(Theme).where(Theme.id == theme_id))).scalar_one_or_none()
    if not theme:
        raise HTTPException(404, "Thème introuvable")

    export_data = {
        "name": theme.name,
        "slug": theme.slug,
        "description": theme.description,
        "author": theme.author,
        "version": theme.version,
        "preview_color": theme.preview_color,
        "preview_bg": theme.preview_bg,
        "css_variables": theme.css_variables,
        "layout": theme.layout,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "format": "b2b-prospector-theme-v1",
    }

    return Response(
        content=json.dumps(export_data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{theme.slug}.theme.json"'},
    )


# ── Helper ──────────────────────────────────────────────────────────

async def _ensure_builtins(db: AsyncSession) -> None:
    """Insère les thèmes builtin s'ils n'existent pas encore."""
    from models.database.theme import Theme

    for bt in BUILTIN_THEMES:
        existing = (await db.execute(select(Theme).where(Theme.slug == bt["slug"]))).scalar_one_or_none()
        if not existing:
            theme = Theme(**{k: v for k, v in bt.items() if k != "is_active"}, is_active=False)
            db.add(theme)

    # S'assure qu'au moins un thème est actif
    active = (await db.execute(select(Theme).where(Theme.is_active.is_(True)))).scalar_one_or_none()
    if not active:
        crmi = (await db.execute(select(Theme).where(Theme.slug == "crmi-light"))).scalar_one_or_none()
        if crmi:
            crmi.is_active = True

    await db.commit()
