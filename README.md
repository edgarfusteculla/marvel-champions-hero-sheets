# Hojas de héroe para Marvel Champions LCG

Fichas de dos caras, en español y listas para imprimir en A4, pensadas para que alguien que
nunca ha jugado a un LCG pueda elegir héroe y saber qué hacer con él desde la primera partida.

- **Cara A — Presentación:** dificultad, potencia, afinidad con cada aspecto según el número de
  jugadores, fortalezas y debilidades.
- **Cara B — Estrategia:** las mejores cartas de firma con imagen y prioridad, las
  circunstanciales, consideraciones y mulligan.

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
| `sections` | Bloques de notas propias. Ver más abajo. |
| `hide` | Apartados que no quieres en esta hoja. Ver más abajo. |
| `variants` | Otras versiones de la misma hoja. Ver más abajo. |
| `strengths`, `weaknesses` | Listas de frases, una caja cada una. |
| `aspects` | Los cuatro aspectos, cada uno valorado de 1 a 5 en `solo`, `duo` y `grupo`. El orden es siempre Agresividad, Justicia, Liderazgo y Protección. |
| `cards` | Lista de `{code, priority, note}`. Las cuatro de mayor prioridad salen como «Mejores cartas»; el resto, como «Cartas circunstanciales». |
| `basics` | Cartas básicas ajenas al kit: `{code, note}`. |
| `consideraciones` | Lista de frases (o de `{chain, text}`). |
| `mulligan` | `{keep: [...], toss: [...]}`. |
| `palette` | Opcional. Por defecto se usan los colores oficiales del héroe que da MarvelCDB. |

El generador valida el archivo antes de dibujar nada y avisa si falta un aspecto, si una
valoración se sale de 1-5 o si un código de carta no pertenece al set de ese héroe.

## Meter tu propia experiencia

Los apuntes en bruto van en `notas/<slug>.md`, que no se imprime: es de donde sale el contenido.
Lo que sí acaba en la hoja se escribe en el JSON, y tienes tres mecanismos.

### Bloques de notas propias

Un apartado con el título que tú quieras, en la cara que tú elijas:

```json
"sections": [
  {
    "title": "Errores típicos de novato",
    "side": "a",
    "tone": "aviso",
    "items": ["Primera nota.", "Segunda nota."]
  }
]
```

`side` es `a` o `b`. `tone` es `consejo` (azul), `aviso` (rojo) o `neutro`.

### Quitar apartados

Si un apartado no aporta para el público de esa hoja, se quita y deja sitio para lo tuyo:

```json
"hide": ["mulligan", "curva"]
```

Se pueden ocultar `fortalezas`, `debilidades`, `aspectos`, `basicas`,
`circunstanciales`, `consideraciones` y `mulligan`.

### Dos versiones del mismo héroe

Una variante es la misma hoja con los cambios que declares. Solo escribes lo que cambia; el
resto se hereda:

```json
"variants": {
  "avanzado": {
    "hide": ["mulligan"],
    "sections": [{ "title": "Detalles finos", "side": "b", "tone": "consejo", "items": ["..."] }]
  }
}
```

Cada variante genera su propio archivo: `dist/spider-man-avanzado.html`. Ojo, una clave declarada
en la variante **sustituye entera** a la de la hoja base, no se fusionan elemento a elemento.

### Cuidado con el espacio

Las dos caras van justas de sitio a propósito: la información entra en A4 sin apretar la
tipografía. Cada nota de carta debería quedarse en unos 70 caracteres, y cada consejo de fase en
unos 65. Un bloque de notas de dos líneas ocupa unos 20 mm, así que casi siempre habrá que
compensarlo con `hide` o acortando textos.

Si te pasas, nada se recorta en silencio: el contenido se va a una tercera página y
`python build.py --pdf` te lo dice y termina con código de salida 2.

```
OK  dist\spider-man.pdf (4 páginas)
AVISO  'spider-man' ocupa 4 páginas en vez de 2: hay contenido que se sale del A4.
```

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
notas/*.md                   Apuntes en bruto, no se imprimen
examples/                    HTML de ejemplo de las hojas ya cerradas
tools/inspect.py             Mide el espacio libre de cada cara y saca un PNG
```

Para ver cuánto sitio queda en una hoja antes de añadir nada:

```bash
python tools/inspect.py dist/spider-man.html
# a=297 libre:93.3 | b=297 libre:7
```

## Notas

- Las imágenes de carta se enlazan desde MarvelCDB y solo existen en inglés, aunque los textos
  de la hoja estén en español.
- Proyecto de aficionados sin ánimo de lucro. Marvel Champions LCG es © Fantasy Flight Games
  y Marvel; los datos e imágenes de carta provienen de MarvelCDB.
