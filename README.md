<!-- /!\ do not modify above this line -->

# solt-odootraining

Repositorio de capacitación y aprendizaje para desarrollo en Odoo.

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

## Addons disponibles

addon | version | maintainers | summary
--- | --- | --- | ---
[solt_library](solt_library/) | 17.0.1.0.0 |  | Módulo de ejemplo: Gestión de biblioteca

[//]: # (end addons)

<!-- prettier-ignore-end -->

## Desarrollo

### Pre-commit

Este repositorio utiliza [pre-commit](https://pre-commit.com/) para ejecutar validaciones automáticas antes de cada commit, asegurando la calidad y consistencia del código.

#### Instalación

1. Instala pre-commit y configura los hooks en tu repositorio local:
```bash
pip install pre-commit
pre-commit install
```

2. (Opcional) Para actualizar los hooks a sus últimas versiones:
```bash
pre-commit autoupdate
```

### Uso

Una vez instalado, pre-commit se ejecutará automáticamente en cada `git commit`. Si alguna validación falla, el commit será bloqueado y se mostrarán los errores encontrados. Algunos hooks corregirán los archivos automáticamente.

Para ejecutar las validaciones manualmente en todos los archivos:
```bash
pre-commit run --all-files
```

### Convenciones de commits

Los mensajes de commit deben seguir la estructura estándar de Odoo/OCA:
```
[TAG] módulo: descripción corta (idealmente < 50 caracteres)

Descripción larga del cambio, incluyendo la razón del mismo.

Enfócate en explicar POR QUÉ se hace el cambio, no QUÉ se cambió
(eso se ve en el diff). Si hubo decisiones técnicas, explica
por qué se tomaron.

task-123
Fixes #123
```

#### Tags permitidos

| Tag | Uso |
|-----|-----|
| `[FIX]` | Corrección de errores |
| `[IMP]` | Mejoras incrementales |
| `[ADD]` | Nuevos módulos o funcionalidades |
| `[REM]` | Eliminación de código o recursos |
| `[REF]` | Refactorización de código |
| `[MOV]` | Mover archivos o código |
| `[REV]` | Revertir commits |
| `[REL]` | Commits de release |
| `[MERGE]` | Commits de merge |
| `[I18N]` | Cambios en traducciones |
| `[PERF]` | Mejoras de rendimiento |
| `[CLN]` | Limpieza de código |
| `[LINT]` | Correcciones de linting |

#### Ejemplos
```
[FIX] solt_library: corregir cálculo de fecha de devolución

La fecha de devolución no consideraba días festivos,
permitiendo préstamos con fechas inválidas.

Fixes #12

[IMP] solt_library: añadir búsqueda por ISBN

Se añade campo ISBN y búsqueda avanzada para facilitar
la localización de libros en el catálogo.

[ADD] solt_library: sistema de reservaciones de libros
```

> **Tip:** El encabezado del commit debe formar una oración válida al concatenarlo con "si se aplica, este commit...". Por ejemplo: "si se aplica, este commit *corregirá el cálculo de fecha de devolución*".

## Licencias

Este repositorio está licenciado bajo [MIT](LICENSE).

Sin embargo, cada módulo puede tener una licencia totalmente diferente. Consulte el archivo `__manifest__.py` de cada módulo, que contiene una clave `license` que explica su licencia.

----

Desarrollado por [Soltein](https://soltein.mx/)