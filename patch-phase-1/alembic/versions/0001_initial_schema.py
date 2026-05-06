"""
Migration initiale - Schéma complet B2B Prospector
Crée toutes les tables nécessaires pour la Phase 1
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum pour les étapes du pipeline
    pipeline_stage_enum = sa.Enum(
        'NOUVEAU', 'CONTACTE', 'RDV_PRIS', 'EN_NEGOCIATION', 'GAGNE', 'PERDU',
        name='pipeline_stage'
    )
    pipeline_stage_enum.create(op.get_bind())

    # Enum pour le scoring
    scoring_enum = sa.Enum('HOT', 'WARM', 'COLD', name='scoring_level')
    scoring_enum.create(op.get_bind())

    # Enum pour le statut des plugins
    plugin_status_enum = sa.Enum('ACTIVE', 'INACTIVE', 'ERROR', name='plugin_status')
    plugin_status_enum.create(op.get_bind())

    # Table users
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), default='user'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Table pipeline_stages
    op.create_table('pipeline_stages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('stage_type', pipeline_stage_enum, nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(length=7), default='#6B7280'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Table prospects
    op.create_table('prospects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('siret', sa.String(length=14), nullable=True),
        sa.Column('siren', sa.String(length=9), nullable=True),
        sa.Column('raison_sociale', sa.String(length=255), nullable=False),
        sa.Column('nom_commercial', sa.String(length=255), nullable=True),
        sa.Column('adresse', sa.String(length=500), nullable=True),
        sa.Column('code_postal', sa.String(length=10), nullable=True),
        sa.Column('ville', sa.String(length=100), nullable=True),
        sa.Column('telephone', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('site_web', sa.String(length=255), nullable=True),
        sa.Column('secteur_activite', sa.String(length=100), nullable=True),
        sa.Column('code_naf', sa.String(length=10), nullable=True),
        sa.Column('effectif', sa.String(length=50), nullable=True),
        sa.Column('chiffre_affaires', sa.String(length=50), nullable=True),
        sa.Column('date_creation', sa.Date(), nullable=True),
        sa.Column('dirigeants', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('score', sa.String(length=20), nullable=True),
        sa.Column('pipeline_stage_id', sa.UUID(), nullable=True),
        sa.Column('pipeline_order', sa.Integer(), default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('source', sa.String(length=50), default='manual'),
        sa.Column('bodacc_mentions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pappers_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('pagesjaunes_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('googlemaps_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['pipeline_stage_id'], ['pipeline_stages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prospects_siret'), 'prospects', ['siret'], unique=False)
    op.create_index(op.f('ix_prospects_siren'), 'prospects', ['siren'], unique=False)
    op.create_index(op.f('ix_prospects_raison_sociale'), 'prospects', ['raison_sociale'], unique=False)

    # Table plugin_states
    op.create_table('plugin_states',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plugin_name', sa.String(length=100), nullable=False),
        sa.Column('status', plugin_status_enum, default='INACTIVE'),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('last_run', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plugin_name')
    )

    # Table audit_logs
    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=True),
        sa.Column('resource_id', sa.UUID(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Table scrape_cache
    op.create_table('scrape_cache',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('identifier', sa.String(length=255), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'identifier', name='uq_scrape_cache_source_identifier')
    )
    op.create_index(op.f('ix_scrape_cache_identifier'), 'scrape_cache', ['identifier'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scrape_cache_identifier'), table_name='scrape_cache')
    op.drop_table('scrape_cache')
    op.drop_table('audit_logs')
    op.drop_table('plugin_states')
    op.drop_index(op.f('ix_prospects_googlemaps_data'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_pagesjaunes_data'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_pappers_data'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_bodacc_mentions'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_source'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_tags'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_notes'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_pipeline_order'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_pipeline_stage_id'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_score'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_date_creation'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_chiffre_affaires'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_effectif'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_code_naf'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_secteur_activite'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_site_web'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_email'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_telephone'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_ville'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_code_postal'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_adresse'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_nom_commercial'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_raison_sociale'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_siren'), table_name='prospects')
    op.drop_index(op.f('ix_prospects_siret'), table_name='prospects')
    op.drop_table('prospects')
    op.drop_table('pipeline_stages')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    sa.Enum(name='plugin_status').drop(op.get_bind())
    sa.Enum(name='scoring_level').drop(op.get_bind())
    sa.Enum(name='pipeline_stage').drop(op.get_bind())
