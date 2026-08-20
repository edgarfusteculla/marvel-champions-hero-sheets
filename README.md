# Hojas de héroe para Marvel Champions LCG

Fichas de dos caras, en español y listas para imprimir en A4, pensadas para que alguien que
nunca ha jugado a un LCG pueda elegir héroe y saber qué hacer con él desde la primera partida.

- **Cara A — Presentación:** dificultad, potencia, estadísticas, puntos fuertes y débiles,
  con qué aspecto acompañarlo y cuál es su obligación.
- **Cara B — Estrategia:** cartas de firma con imagen y prioridad, combos, curva de coste,
  qué quedarse en la mano inicial y plan de juego por fases.

Cada héroe se describe en un único archivo JSON. Los datos objetivos de las cartas (nombre en
español, coste, tipo, texto, imagen y colores del héroe) se descargan de
[MarvelCDB](https://es.marvelcdb.com), así que en el JSON solo escribes lo que es criterio tuyo:
valoraciones, prioridades, combos y consejos.

## Puesta en marcha

```bash
pip install -r requirements.txt
python build.py                     # genera todas las hojas en dist/
python build.py spider-man --open   # genera una y la abre en el navegador
python build.py --pdf               # genera además el PDF (necesita Edge o Chrome)
python build.py --refresh           # vuelve a descargar los datos de MarvelCDB
```

Las respuestas de MarvelCDB se guardan en `cache/`, de modo que después de la primera
generación el proceso funciona sin conexión.

### Imprimir

Imprime a doble cara con **márgenes: ninguno** y **gráficos de fondo: activados**. La hoja mide
210 × 297 mm exactos y el HTML declara `@page { size: A4; margin: 0 }`, así que salen dos
páginas justas, sin ninguna en blanco.

## Añadir un héroe

Crea `data/heroes/<slug>.json` copiando el de Spider-Man. Lo único que necesitas buscar es el
código de la carta de héroe en MarvelCDB: aparece en la URL de la carta
(`marvelcdb.com/card/01001a` → `01001a`). A partir de ahí, el resto de su set de firma se
descubre solo.

| Campo | Qué es |
| --- | --- |
| `slug` | Nombre del archivo de salida. |
| `hero_card_code` | Código de la carta de héroe en MarvelCDB. |
| `display_name`, `alter_ego_name` | Opcionales, para forzar cómo se escribe el nombre. |
| `difficulty`, `power` | Enteros de 1 a 5. |
| `beginner_friendly` | Si es `true`, se imprime el distintivo de héroe recomendado. |
| `playstyle` | La frase destacada del pie de la cara A. |
| `strengths`, `weaknesses` | Listas de frases. |
| `aspects` | Los cuatro aspectos, cada uno con `rating` (1-5) y `note`. Se ordenan solos de mejor a peor. |
| `cards` | Lista de `{code, priority, note}`. Las cuatro de mayor prioridad salen a tamaño grande. |
| `combos` | Lista de `{chain, text}`. |
| `mulligan` | `{keep: [...], toss: [...]}`. |
| `phases` | `{early: [...], mid: [...], late: [...]}`. |
| `palette` | Opcional. Por defecto se usan los colores oficiales del héroe que da MarvelCDB. |

El generador valida el archivo antes de dibujar nada y avisa si falta un aspecto, si una
valoración se sale de 1-5 o si un código de carta no pertenece al set de ese héroe.

### Cuidado con el espacio

Las dos caras van justas de sitio a propósito: la información entra en A4 sin apretar la
tipografía. Si al añadir texto ves que algo se corta, acorta las notas antes que reducir el
tamaño de letra. Cada nota de carta debería quedarse en unos 70 caracteres, y cada consejo de
fase en unos 65.

## Estructura

```
build.py                     Punto de entrada
mchs/marvelcdb.py            Cliente de la API con caché en disco
mchs/heroes.py               Carga y validación de los JSON de héroe
mchs/render.py               Mezcla datos + criterio editorial y renderiza
mchs/pdf.py                  Exportación a PDF con navegador headless
templates/hero_sheet.html.j2 Maquetación de las dos caras
templates/sheet.css          Estilos (en milímetros, pensados para impresión)
data/heroes/*.json           Un archivo por héroe
```

## Notas

- Las imágenes de carta se enlazan desde MarvelCDB y solo existen en inglés, aunque los textos
  de la hoja estén en español.
- Proyecto de aficionados sin ánimo de lucro. Marvel Champions LCG es © Fantasy Flight Games
  y Marvel; los datos e imágenes de carta provienen de MarvelCDB.
