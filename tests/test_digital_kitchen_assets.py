from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def test_digital_kitchen_entrypoint_references_local_assets():
    html = (APP / "index.html").read_text(encoding="utf-8")
    assert '<link rel="stylesheet" href="./styles.css">' in html
    assert '<script src="./app.js"></script>' in html
    assert "Research Kitchen" in html


def test_digital_kitchen_has_required_workspace_regions():
    html = (APP / "index.html").read_text(encoding="utf-8")
    for marker in (
        'class="sidebar"',
        'class="workbench"',
        'class="researcher-panel"',
        'id="ingredientGrid"',
        'id="researchPrompt"',
        'id="prepareBrief"',
        'id="briefDialog"',
    ):
        assert marker in html


def test_frontend_discloses_unconnected_science_boundary():
    html = (APP / "index.html").read_text(encoding="utf-8")
    readme = (APP / "README.md").read_text(encoding="utf-8")
    assert "scientific simulations are not connected yet" in html
    assert "does not call an LLM" in readme
    assert "does not" in readme and "food-science solver" in readme


def test_frontend_script_uses_safe_text_insertion_for_user_ingredients():
    script = (APP / "app.js").read_text(encoding="utf-8")
    assert "title.textContent = name" in script
    assert "detail.textContent" in script
    assert "innerHTML" not in script
