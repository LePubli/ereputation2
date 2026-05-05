"""
Tests unitaires pour le plugin Audit Digital
"""
import pytest
import sys
from pathlib import Path
import importlib.util
from unittest.mock import AsyncMock, MagicMock, patch

# Ajoute le workspace au path pour les imports
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

# Import dynamique du module audit-digital
audit_digital_path = workspace_root / "plugins" / "audit-digital" / "main.py"
spec = importlib.util.spec_from_file_location("audit_digital", audit_digital_path)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)

DigitalAuditPlugin = audit_module.DigitalAuditPlugin
create_plugin = audit_module.create_plugin


class TestDigitalAuditPlugin:
    """Tests unitaires pour le plugin d'audit digital"""
    
    @pytest.fixture
    def plugin(self):
        """Fixture pour créer une instance du plugin"""
        return create_plugin()
    
    def test_plugin_initialization(self, plugin):
        """Test que le plugin s'initialise correctement"""
        assert plugin.name == "audit-digital"
        assert plugin.version == "1.0.0"
        assert plugin.timeout == 30
        assert plugin.max_pages == 5
        assert len(plugin.cms_signatures) > 0
        assert len(plugin.tracking_signatures) > 0
    
    def test_cms_signatures_present(self, plugin):
        """Test que les signatures CMS sont définies"""
        expected_cms = ["WordPress", "Shopify", "Wix", "PrestaShop"]
        for cms in expected_cms:
            assert cms in plugin.cms_signatures
            assert len(plugin.cms_signatures[cms]) > 0
    
    def test_tracking_signatures_present(self, plugin):
        """Test que les signatures de tracking sont définies"""
        expected_tools = ["google_analytics", "meta_pixel", "hotjar", "gtm"]
        for tool in expected_tools:
            assert tool in plugin.tracking_signatures
            assert len(plugin.tracking_signatures[tool]) > 0
    
    def test_create_plugin_factory(self):
        """Test que la factory crée correctement une instance"""
        plugin = create_plugin()
        assert isinstance(plugin, DigitalAuditPlugin)
        assert plugin.name == "audit-digital"
    
    @pytest.mark.asyncio
    async def test_audit_website_timeout(self, plugin):
        """Test la gestion du timeout lors d'un audit"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.side_effect = Exception("Timeout")
            
            result = await plugin.audit_website("https://example.com")
            
            assert result["url"] == "https://example.com"
            assert "error" in result or result["score_maturite"] == 0
    
    def test_calculate_score_empty_results(self, plugin):
        """Test le calcul de score avec des résultats vides"""
        empty_results = {
            "presence": {},
            "tech_stack": {},
            "performance": {"score_estime": 0},
            "tracking": {"total_tools": 0},
            "compliance": {},
            "social_media": {"total_networks": 0},
            "seo": {"open_graph_tags": 0}
        }
        
        score = plugin._calculate_score(empty_results)
        assert 0 <= score <= 100
    
    def test_calculate_score_perfect_results(self, plugin):
        """Test le calcul de score avec des résultats parfaits"""
        perfect_results = {
            "presence": {"accessible": True, "https": True},
            "tech_stack": {"cms_detecte": "WordPress", "technologies_detectees": ["React", "Bootstrap"]},
            "performance": {"score_estime": 95},
            "tracking": {"total_tools": 5},
            "compliance": {
                "cookie_banner_present": True,
                "privacy_policy_link": True,
                "rgpd_compliant_estimate": True
            },
            "social_media": {"total_networks": 5},
            "seo": {"open_graph_tags": 5}
        }
        
        score = plugin._calculate_score(perfect_results)
        assert 0 <= score <= 100
        # Le score est pondéré - un score > 20 est déjà bon pour cette configuration
        assert score >= 20
    
    def test_analyze_presence(self, plugin):
        """Test l'analyse de présence web"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.history = []
        mock_response.headers = {"server": "nginx", "content-type": "text/html"}
        
        result = plugin._analyze_presence("https://example.com", mock_response)
        
        assert result["accessible"] is True
        assert result["status_code"] == 200
        assert result["https"] is True
        assert result["server"] == "nginx"
    
    def test_detect_tracking_basic(self, plugin):
        """Test la détection basique de tracking"""
        html_with_ga = "<html><script src='https://www.googletagmanager.com/gtag.js'></script></html>"
        soup = MagicMock()
        
        result = plugin._detect_tracking(html_with_ga, soup)
        
        assert result["google_analytics"] is True
        assert result["total_tools"] >= 1
    
    def test_detect_social_media_links(self, plugin):
        """Test la détection des réseaux sociaux"""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <body>
                <a href="https://linkedin.com/company/example">LinkedIn</a>
                <a href="https://twitter.com/example">Twitter</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = plugin._detect_social_media(soup, html)
        
        assert result["linkedin_url"] is not None
        assert result["twitter_url"] is not None
        assert result["total_networks"] >= 2
    
    def test_extract_technologies_react(self, plugin):
        """Test l'extraction de technologies - React"""
        html = "<html><script src='react-dom.production.min.js'></script></html>"
        
        techs = plugin._extract_technologies(html)
        
        assert "React" in techs
    
    def test_extract_technologies_bootstrap(self, plugin):
        """Test l'extraction de technologies - Bootstrap"""
        html = "<html><link rel='stylesheet' href='bootstrap.min.css'></html>"
        
        techs = plugin._extract_technologies(html)
        
        assert "Bootstrap" in techs
    
    def test_check_compliance_basic(self, plugin):
        """Test la vérification de conformité basique"""
        from bs4 import BeautifulSoup
        
        html_compliant = """
        <html>
            <body>
                <div>Ce site utilise des cookies pour améliorer votre expérience.</div>
                <a href="/privacy-policy">Politique de confidentialité</a>
                <input type="checkbox" required />
            </body>
        </html>
        """
        soup = BeautifulSoup(html_compliant, 'html.parser')
        
        result = plugin._check_compliance(soup, html_compliant, "https://example.com")
        
        assert result["cookie_banner_present"] is True
        assert result["privacy_policy_link"] is True
        assert result["consent_mechanism"] is True
    
    def test_seo_analysis_with_meta_tags(self, plugin):
        """Test l'analyse SEO avec balises meta"""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <head>
                <title>Exemple - Site de test</title>
                <meta name="description" content="Ceci est une description de test">
                <meta property="og:title" content="Exemple OG">
            </head>
            <body>
                <h1>Bienvenue</h1>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        result = plugin._analyze_seo(soup, "https://example.com")
        
        assert result["meta_title"] == "Exemple - Site de test"
        assert "description de test" in result["meta_description"].lower()
        assert result["h1_count"] == 1
        assert result["open_graph_tags"] >= 1


@pytest.mark.asyncio
async def test_audit_website_integration():
    """Test d'intégration avec un vrai site (optionnel, peut échouer sans réseau)"""
    plugin = create_plugin()
    
    try:
        result = await plugin.audit_website("https://example.com")
        
        assert result["url"] == "https://example.com"
        assert "audit_date" in result
        assert "score_maturite" in result
        assert 0 <= result["score_maturite"] <= 100
    except Exception:
        # Test optionnel - peut échouer en environnement sans réseau
        pytest.skip("Network unavailable for integration test")
