"""Mide y captura las hojas generadas con el navegador headless.

Uso:
    python tools/inspect.py dist/spider-man.html
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mchs.pdf import find_browser

PROBE = """
<script>
window.addEventListener('load', () => {
  const mm = v => Math.round(v / 3.7795 * 10) / 10;
  const out = [...document.querySelectorAll('.sheet')].map(s => {
    const body = s.querySelector('.body');
    const used = [...body.children].reduce((t, c) => t + c.getBoundingClientRect().height, 0)
      + parseFloat(getComputedStyle(body).rowGap || 0) * (body.children.length - 1);
    return s.className.slice(-1) + '=' + mm(s.getBoundingClientRect().height)
      + ' libre:' + mm(body.getBoundingClientRect().height - used);
  });
  document.title = 'MEDIDAS ' + out.join(' | ');
});
</script>
"""


def main() -> int:
    source = Path(sys.argv[1]).resolve()
    browser = find_browser()
    html = source.read_text(encoding="utf-8").replace("</head>", PROBE + "</head>")

    with tempfile.TemporaryDirectory() as tmp:
        probe_file = Path(tmp) / source.name
        probe_file.write_text(html, encoding="utf-8")
        dump = subprocess.run(
            [
                browser, "--headless", "--disable-gpu", "--no-sandbox",
                "--virtual-time-budget=8000", "--dump-dom", probe_file.as_uri(),
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        found = re.search(r"MEDIDAS ([^<]+)", dump.stdout or "")
        print(found.group(1).strip() if found else "no se pudo medir")

        shot = source.with_suffix(".png")
        subprocess.run(
            [
                browser, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                "--virtual-time-budget=8000", "--window-size=794,2400",
                f"--screenshot={shot}", source.as_uri(),
            ],
            capture_output=True, text=True,
        )
        print(shot if shot.exists() else "no se pudo capturar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
