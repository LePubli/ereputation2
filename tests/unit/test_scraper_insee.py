"""
Tests unitaires pour le plugin scraper-insee
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


class TestScraperINSEE:
    """Tests du plugin scraper-insee"""
    
    @pytest.mark.asyncio
    async def test_get_insee_token(self):
        """Test de récupération du token INSEE"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "test_token_123"}
            mock_post.return_value = mock_response
            
            token = await scraper._get_insee_token()
            
            assert token == "test_token_123"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_company_data_success(self):
        """Test de récupération des données entreprise (succès)"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        scraper.insee_token = "valid_token"
        
        mock_data = {
            "uniteLegale": {
                "siren": "123456789",
                "denominationUniteLegale": "TEST COMPANY",
                "codePostalUniteLegale": "75001",
                "libelleCommuneUniteLegale": "Paris",
                "activitePrincipaleUniteLegale": "6201Z",
                "trancheEffectifsUniteLegale": "10"
            }
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            result = await scraper.fetch_company_data("123456789")
            
            assert result is not None
            assert result["siren"] == "123456789"
            assert result["raison_sociale"] == "TEST COMPANY"
    
    @pytest.mark.asyncio
    async def test_fetch_company_data_not_found(self):
        """Test de récupération des données (entreprise non trouvée)"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await scraper.fetch_company_data("999999999")
            
            assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_pappers_fallback(self):
        """Test du fallback vers Pappers API"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        scraper.use_insee = False  # Forcer Pappers
        
        mock_data = {
            "siren": "123456789",
            "nom": "PAPPERS TEST",
            "ville": "Lyon"
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response
            
            result = await scraper._fetch_from_pappers("123456789")
            
            assert result is not None
            mock_get.assert_called_once()
    
    def test_validate_siren_format(self):
        """Test de validation du format SIREN"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        # SIREN valide (9 chiffres)
        assert scraper._validate_siren("123456789") is True
        assert scraper._validate_siren("000000001") is True
        
        # SIREN invalide
        assert scraper._validate_siren("12345678") is False  # Trop court
        assert scraper._validate_siren("1234567890") is False  # Trop long
        assert scraper._validate_siren("12345678A") is False  # Contient une lettre
        assert scraper._validate_siren("") is False  # Vide
    
    def test_siren_to_siret_conversion(self):
        """Test de conversion SIREN → SIRET"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        # SIREN + NIC (numéro interne) = SIRET
        siren = "123456789"
        nic = "00012"
        
        siret = scraper._siren_to_siret(siren, nic)
        
        assert siret == "12345678900012"
        assert len(siret) == 14
    
    def test_cache_mechanism(self):
        """Test du mécanisme de cache"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        # Ajouter au cache
        test_data = {"siren": "123456789", "test": "value"}
        scraper._cache_set("123456789", test_data)
        
        # Récupérer du cache
        cached = scraper._cache_get("123456789")
        
        assert cached is not None
        assert cached["siren"] == "123456789"
        assert cached["test"] == "value"
        
        # Clé inexistante
        missing = scraper._cache_get("999999999")
        assert missing is None


class TestScraperINSEESearch:
    """Tests de recherche d'entreprises"""
    
    @pytest.mark.asyncio
    async def test_search_by_name(self):
        """Test de recherche par nom d'entreprise"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        mock_results = [
            {"siren": "111111111", "nom": "Company A"},
            {"siren": "222222222", "nom": "Company B"},
        ]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": mock_results}
            mock_get.return_value = mock_response
            
            results = await scraper.search_by_name("Company")
            
            assert len(results) == 2
            assert any(r["siren"] == "111111111" for r in results)
    
    @pytest.mark.asyncio
    async def test_search_by_naf_code(self):
        """Test de recherche par code NAF"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        mock_results = [
            {"siren": "333333333", "naf": "6201Z"},
            {"siren": "444444444", "naf": "6201Z"},
        ]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": mock_results}
            mock_get.return_value = mock_response
            
            results = await scraper.search_by_naf("6201Z")
            
            assert len(results) == 2
            assert all(r["naf"] == "6201Z" for r in results)
    
    def test_search_query_validation(self):
        """Test de validation des requêtes de recherche"""
        from plugins.scraper-insee.main import ScraperINSEE
        
        scraper = ScraperINSEE()
        
        # Requête valide
        assert scraper._validate_query("Company Name") is True
        assert scraper._validate_query("Tech SAS") is True
        
        # Requête trop courte
        assert scraper._validate_query("AB") is False
        
        # Requête avec caractères spéciaux dangereux
        assert scraper._validate_query("<script>") is False


# Run tests with: pytest tests/unit/test_scraper_insee.py -v
