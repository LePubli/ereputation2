"""
Plugin Audit Digital - Analyse complète de la présence digitale
Scanne les sites web, détecte la tech stack, analyse SEO, performance, pixels tracking et conformité RGPD
"""
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger
from urllib.parse import urlparse, urljoin
import re


class DigitalAuditPlugin:
    """
    Plugin d'audit digital complet
    Analyse: CMS, hébergeur, performance, SEO, pixels tracking, réseaux sociaux, conformité RGPD
    """
    
    def __init__(self):
        self.name = "audit-digital"
        self.version = "1.0.0"
        self.timeout = 30
        self.max_pages = 5
        self.user_agent = "B2BProspector/1.0 (Digital Audit Bot)"
        
        # Signatures de détection CMS
        self.cms_signatures = {
            "WordPress": ["wp-content", "wp-includes", "wp-json"],
            "Shopify": ["shopify", "cdn.shopify.com"],
            "Wix": ["wix.com", "wixstatic.com"],
            "Squarespace": ["squarespace.com", "static.squarespace.com"],
            "PrestaShop": ["prestashop", "themes/prestashop"],
            "Joomla": ["media/jui", "components/com_"],
            "Drupal": ["sites/all", "drupal.js"],
            "Webflow": ["webflow.com", "assets.website-files.com"],
        }
        
        # Signatures de pixels/analytics
        self.tracking_signatures = {
            "google_analytics": ["googletagmanager.com", "analytics.js", "gtag.js", "GA_TRACKING_ID"],
            "meta_pixel": ["facebook.net", "connect.facebook.net", "fbevents.js"],
            "hotjar": ["hotjar.com", "static.hotjar.com"],
            "gtm": ["googletagmanager.com/gtm.js"],
            "linkedin_insight": ["snap.licdn.com/li.lms-analytics/insight.min.js"],
            "twitter_pixel": ["analytics.twitter.com"],
        }
        
    async def audit_website(self, url: str) -> Dict[str, Any]:
        """
        Lance un audit complet d'un site web
        Args:
            url: URL du site à auditer
        Returns:
            Dictionnaire contenant tous les résultats d'audit
        """
        logger.info(f"Starting digital audit for: {url}")
        
        results = {
            "url": url,
            "audit_date": datetime.utcnow().isoformat(),
            "presence": {},
            "tech_stack": {},
            "performance": {},
            "seo": {},
            "tracking": {},
            "social_media": {},
            "compliance": {},
            "score_maturite": 0,
            "details": []
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True
            ) as client:
                # Récupération de la page principale
                response = await client.get(url)
                html_content = response.text
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 1. Analyse présence & HTTPS
                results["presence"] = self._analyze_presence(url, response)
                
                # 2. Détection CMS & Tech Stack
                results["tech_stack"] = self._detect_tech_stack(html_content, soup, url)
                
                # 3. Analyse Performance (Core Web Vitals estimés)
                results["performance"] = await self._analyze_performance(url, html_content, soup)
                
                # 4. Analyse SEO
                results["seo"] = self._analyze_seo(soup, url)
                
                # 5. Détection Pixels & Tracking
                results["tracking"] = self._detect_tracking(html_content, soup)
                
                # 6. Détection Réseaux Sociaux
                results["social_media"] = self._detect_social_media(soup, html_content)
                
                # 7. Vérification Conformité RGPD
                results["compliance"] = self._check_compliance(soup, html_content, url)
                
                # 8. Calcul du score global
                results["score_maturite"] = self._calculate_score(results)
                
                logger.info(f"Audit completed - Score: {results['score_maturite']}/100")
                
        except httpx.TimeoutException:
            logger.warning(f"Timeout during audit of {url}")
            results["error"] = "Timeout - Site trop lent ou indisponible"
        except httpx.RequestError as e:
            logger.error(f"Request error during audit of {url}: {e}")
            results["error"] = f"Erreur de connexion: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during audit of {url}: {e}")
            results["error"] = f"Erreur inattendue: {str(e)}"
        
        return results
    
    def _analyze_presence(self, url: str, response) -> Dict[str, Any]:
        """Analyse la présence web de base"""
        parsed = urlparse(url)
        
        return {
            "accessible": response.status_code < 400,
            "status_code": response.status_code,
            "https": parsed.scheme == "https",
            "redirect_chain": [str(r.url) for r in response.history] if response.history else [],
            "server": response.headers.get("server", "unknown"),
            "content_type": response.headers.get("content-type", "unknown"),
        }
    
    def _detect_tech_stack(self, html: str, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Détecte le CMS et les technologies utilisées"""
        detected_cms = None
        cms_confidence = 0
        
        # Détection CMS par signatures
        for cms, signatures in self.cms_signatures.items():
            matches = sum(1 for sig in signatures if sig in html.lower())
            if matches > 0 and matches > cms_confidence:
                detected_cms = cms
                cms_confidence = matches
        
        # Détection hébergeur via headers ou DNS (simplifié)
        hebergeur = "unknown"
        server_header = soup.find_all(string=re.compile(r"cloudflare|aws|nginx|apache|iis"))
        if server_header:
            hebergeur = str(server_header[0])
        
        return {
            "cms_detecte": detected_cms,
            "cms_confidence": cms_confidence,
            "hebergeur": hebergeur,
            "technologies_detectees": self._extract_technologies(html),
        }
    
    def _extract_technologies(self, html: str) -> List[str]:
        """Extrait les technologies détectées dans le HTML"""
        techs = []
        
        # Frameworks JS
        if "react" in html.lower() or "react-dom" in html.lower():
            techs.append("React")
        if "vue.js" in html.lower() or "vuejs" in html.lower():
            techs.append("Vue.js")
        if "angular" in html.lower():
            techs.append("Angular")
        
        # CSS frameworks
        if "bootstrap" in html.lower():
            techs.append("Bootstrap")
        if "tailwind" in html.lower():
            techs.append("Tailwind CSS")
        
        # jQuery
        if "jquery" in html.lower():
            techs.append("jQuery")
        
        return techs
    
    async def _analyze_performance(self, url: str, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyse les performances (estimation Core Web Vitals)"""
        # Estimation basée sur la taille et complexité du HTML
        html_size = len(html)
        images = soup.find_all('img')
        scripts = soup.find_all('script')
        stylesheets = soup.find_all('link', rel='stylesheet')
        
        # Score estimé (simplifié - en prod utiliser Lighthouse API)
        size_penalty = min(30, html_size / 10000)
        image_penalty = min(20, len(images) * 2)
        script_penalty = min(20, len(scripts) * 3)
        
        estimated_score = max(0, 100 - size_penalty - image_penalty - script_penalty)
        
        return {
            "score_estime": int(estimated_score),
            "html_size_kb": round(html_size / 1024, 2),
            "images_count": len(images),
            "scripts_count": len(scripts),
            "stylesheets_count": len(stylesheets),
            "lcp_estime": "good" if estimated_score > 75 else "needs_improvement",
            "fid_estime": "good" if len(scripts) < 10 else "needs_improvement",
            "cls_estime": "good" if len(images) < 20 else "needs_improvement",
        }
    
    def _analyze_seo(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Analyse les éléments SEO on-page"""
        # Meta title
        title = soup.find('title')
        meta_title = title.string.strip() if title else None
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc.get('content') if meta_desc else None
        
        # H1
        h1_tags = soup.find_all('h1')
        
        # Sitemap & Robots
        sitemap_present = False
        robots_present = False
        
        # Vérification simplifiée (en prod, faire requêtes HTTP)
        base_url = urlparse(url).scheme + "://" + urlparse(url).netloc
        if soup.find(string=re.compile(r"sitemap.xml")):
            sitemap_present = True
        if soup.find(string=re.compile(r"robots.txt")):
            robots_present = True
        
        # Open Graph
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        
        return {
            "meta_title": meta_title,
            "meta_title_length": len(meta_title) if meta_title else 0,
            "meta_description": meta_description,
            "meta_description_length": len(meta_description) if meta_description else 0,
            "h1_count": len(h1_tags),
            "h1_text": [h1.get_text().strip() for h1 in h1_tags],
            "sitemap_present": sitemap_present,
            "robots_present": robots_present,
            "open_graph_tags": len(og_tags),
            "canonical": soup.find('link', rel='canonical'),
        }
    
    def _detect_tracking(self, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Détecte les outils de tracking et analytics"""
        tracking_detected = {}
        
        for tool, signatures in self.tracking_signatures.items():
            detected = any(sig in html.lower() for sig in signatures)
            tracking_detected[tool] = detected
        
        # Détection supplémentaire
        gtm_id = re.search(r'GTM-[A-Z0-9]+', html)
        ga_id = re.search(r'UA-\d+-\d+|G-[A-Z0-9]+', html)
        
        return {
            "google_analytics": tracking_detected.get("google_analytics", False),
            "ga_tracking_id": ga_id.group(0) if ga_id else None,
            "meta_pixel": tracking_detected.get("meta_pixel", False),
            "hotjar": tracking_detected.get("hotjar", False),
            "gtm": tracking_detected.get("gtm", False),
            "gtm_id": gtm_id.group(0) if gtm_id else None,
            "linkedin_insight": tracking_detected.get("linkedin_insight", False),
            "twitter_pixel": tracking_detected.get("twitter_pixel", False),
            "total_tools": sum(1 for v in tracking_detected.values() if v),
        }
    
    def _detect_social_media(self, soup: BeautifulSoup, html: str) -> Dict[str, Any]:
        """Détecte les liens vers les réseaux sociaux"""
        social_urls = {
            "linkedin": None,
            "facebook": None,
            "twitter": None,
            "instagram": None,
            "youtube": None,
        }
        
        # Recherche dans les liens
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if 'linkedin.com' in href:
                social_urls["linkedin"] = link['href']
            elif 'facebook.com' in href or 'fb.com' in href:
                social_urls["facebook"] = link['href']
            elif 'twitter.com' in href or 'x.com' in href:
                social_urls["twitter"] = link['href']
            elif 'instagram.com' in href:
                social_urls["instagram"] = link['href']
            elif 'youtube.com' in href or 'youtu.be' in href:
                social_urls["youtube"] = link['href']
        
        # Détection via meta tags
        if not social_urls["linkedin"]:
            linkedin_meta = soup.find('meta', property='article:author')
            if linkedin_meta:
                social_urls["linkedin"] = linkedin_meta.get('content')
        
        present_networks = [k for k, v in social_urls.items() if v]
        
        return {
            "linkedin_url": social_urls["linkedin"],
            "facebook_url": social_urls["facebook"],
            "twitter_url": social_urls["twitter"],
            "instagram_url": social_urls["instagram"],
            "youtube_url": social_urls["youtube"],
            "networks_present": present_networks,
            "total_networks": len(present_networks),
        }
    
    def _check_compliance(self, soup: BeautifulSoup, html: str, url: str) -> Dict[str, Any]:
        """Vérifie la conformité RGPD et email"""
        # Cookies banner
        cookie_banner = bool(soup.find_all(string=re.compile(r"cookie|consentement|confidentialité", re.I)))
        
        # Politique de confidentialité
        privacy_link = soup.find('a', href=re.compile(r"privacy|confidentialit|rgpd|donnees", re.I))
        
        # SPF/DKIM/DMARC (vérification DNS simplifiée - en prod faire vraie vérif)
        spf_present = bool(re.search(r'v=spf1', html, re.I))
        
        # Formulaire avec consentement
        consent_checkbox = bool(soup.find('input', type='checkbox', attrs={'required': True}))
        
        return {
            "cookie_banner_present": cookie_banner,
            "privacy_policy_link": bool(privacy_link),
            "spf_configured": spf_present,
            "dkim_configured": False,  # Nécessite vérification DNS
            "dmarc_configured": False,  # Nécessite vérification DNS
            "consent_mechanism": consent_checkbox,
            "rgpd_compliant_estimate": cookie_banner and bool(privacy_link),
        }
    
    def _calculate_score(self, results: Dict[str, Any]) -> int:
        """
        Calcule le score de maturité digitale (0-100)
        Basé sur les poids définis dans le manifest
        """
        score = 0
        
        # Présence (30 points)
        presence_score = 0
        if results["presence"].get("accessible"):
            presence_score += 15
        if results["presence"].get("https"):
            presence_score += 15
        score += presence_score * 0.30
        
        # Modernité (25 points)
        modernity_score = 0
        if results["tech_stack"].get("cms_detecte"):
            modernity_score += 10
        if results["tech_stack"].get("technologies_detectees"):
            modernity_score += 5
        perf_score = results["performance"].get("score_estime", 0)
        modernity_score += (perf_score / 100) * 10
        score += modernity_score * 0.25
        
        # Tracking (20 points)
        tracking_count = results["tracking"].get("total_tools", 0)
        tracking_score = min(20, tracking_count * 5)
        score += tracking_score * 0.20
        
        # Conformité (15 points)
        compliance_score = 0
        if results["compliance"].get("cookie_banner_present"):
            compliance_score += 5
        if results["compliance"].get("privacy_policy_link"):
            compliance_score += 5
        if results["compliance"].get("rgpd_compliant_estimate"):
            compliance_score += 5
        score += compliance_score * 0.15
        
        # Engagement (10 points)
        social_count = results["social_media"].get("total_networks", 0)
        engagement_score = min(10, social_count * 2)
        seo_score = min(5, results["seo"].get("open_graph_tags", 0))
        score += (engagement_score + seo_score) * 0.10
        
        return min(100, int(score))


def create_plugin() -> DigitalAuditPlugin:
    """Factory pour créer une instance du plugin"""
    return DigitalAuditPlugin()


# Routes API
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/audit", tags=["Digital Audit"])


class AuditRequest(BaseModel):
    url: str
    prospect_id: Optional[str] = None


@router.post("/{prospect_id}")
async def start_digital_audit(prospect_id: str, request: AuditRequest) -> Dict[str, Any]:
    """Lancer un audit digital complet"""
    try:
        plugin = create_plugin()
        url = request.url or f"https://prospect-{prospect_id}.fr"
        
        results = await plugin.audit_website(url)
        
        return {
            "success": True,
            "prospect_id": prospect_id,
            "audit_date": results.get("audit_date"),
            "score_maturite": results.get("score_maturite"),
            "summary": {
                "cms": results.get("tech_stack", {}).get("cms_detecte"),
                "https": results.get("presence", {}).get("https"),
                "tracking_tools": results.get("tracking", {}).get("total_tools"),
                "social_networks": results.get("social_media", {}).get("total_networks"),
                "rgpd_compliant": results.get("compliance", {}).get("rgpd_compliant_estimate"),
            },
            "full_results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.get("/{prospect_id}")
async def get_digital_audit(prospect_id: str) -> Dict[str, Any]:
    """Récupérer les résultats d'un audit existant (mock pour MVP)"""
    # Dans une implémentation complète, récupérer depuis la database
    return {
        "success": True,
        "prospect_id": prospect_id,
        "message": "Audit non trouvé - Veuillez lancer un audit avec POST",
        "note": "Endpoint mock pour MVP - Implémenter persistance DB"
    }


@router.get("/{prospect_id}/score")
async def get_digital_score(prospect_id: str) -> Dict[str, Any]:
    """Obtenir uniquement le score de maturité digitale"""
    return {
        "success": True,
        "prospect_id": prospect_id,
        "score_maturite": 0,
        "message": "Score non disponible - Veuillez lancer un audit avec POST"
    }


def init():
    """Initialisation du plugin"""
    logger.info("Digital Audit plugin initialized")


def cleanup():
    """Cleanup du plugin"""
    logger.info("Digital Audit plugin cleanup complete")
