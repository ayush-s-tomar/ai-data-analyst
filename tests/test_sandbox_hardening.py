import pytest

from sandbox import CodeRejected, validate_code


@pytest.mark.parametrize("code", [
    "g = (1 for _ in [0])\nx = g.gi_frame",
    "x = df.sum.f_globals",
    "import string",
    "df.to_json('out.json')",
    "df.to_xml('out.xml')",
    "df.to_latex('out.tex')",
    "df.values.dump('x.bin')",
    "plt.gcf().canvas.print_png('x.png')",
])
def test_hardening_rejects_known_escape_routes(code):
    with pytest.raises(CodeRejected):
        validate_code(code)
