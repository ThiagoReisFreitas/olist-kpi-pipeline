import pytest
from dashboard.app import kpi, header, section, TEAL, CORAL, BLUE, AMBER, PURPLE


class TestKpi:
    def test_contains_value(self):
        result = kpi("89.6%", "OTD médio", "🎯")
        assert "89.6%" in result

    def test_contains_label(self):
        result = kpi("89.6%", "OTD médio", "🎯")
        assert "OTD médio" in result

    def test_contains_icon(self):
        result = kpi("42", "Pedidos", "🛒")
        assert "🛒" in result

    def test_default_color_is_teal(self):
        result = kpi("10", "label")
        assert TEAL in result

    def test_custom_color_applied(self):
        result = kpi("10", "label", color=CORAL)
        assert CORAL in result

    def test_returns_html_string(self):
        result = kpi("10", "label")
        assert result.strip().startswith("<div")
        assert "kpi-card" in result

    def test_color_appears_in_border_and_value(self):
        result = kpi("99", "teste", color=PURPLE)
        assert result.count(PURPLE) >= 2


class TestHeader:
    def test_contains_title(self):
        result = header("Visão Geral")
        assert "Visão Geral" in result

    def test_contains_subtitle_when_provided(self):
        result = header("Título", "Subtítulo aqui")
        assert "Subtítulo aqui" in result
        assert "page-subtitle" in result

    def test_no_subtitle_tag_when_omitted(self):
        result = header("Só título")
        assert "page-subtitle" not in result

    def test_returns_html_string(self):
        result = header("X")
        assert "page-header" in result
        assert "page-title" in result


class TestSection:
    def test_contains_text(self):
        result = section("OTD por estado")
        assert "OTD por estado" in result

    def test_uses_section_label_class(self):
        result = section("qualquer coisa")
        assert "section-label" in result

    def test_returns_div(self):
        result = section("x")
        assert result.strip().startswith("<div")
