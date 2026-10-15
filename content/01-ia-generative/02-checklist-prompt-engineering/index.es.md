---
title: Checklist de ingeniería de prompts
description: Las comprobaciones que hay que hacer antes de llevar un prompt a producción.
tags: [prompt, gemini, buenas-practicas]
level: beginner
date: 2026-09-15
---

Un buen prompt se revisa como una especificación. Antes de entregarlo, repasa esta lista.

## Contenido del prompt

- [ ] El rol y el objetivo aparecen en la primera frase.
- [ ] Se indican el público y el tono.
- [ ] El formato de salida es explícito (JSON, Markdown, longitud máxima).
- [ ] Dos o tres ejemplos (*few-shot*) cubren los casos típicos **y** un caso límite.

## Robustez

- [ ] Los datos del usuario están separados de las instrucciones.
- [ ] El modelo sabe qué responder cuando falta información.
- [ ] La temperatura es adecuada a la tarea.

## Evaluación

- [ ] Hay un conjunto de 20 a 50 casos de prueba versionado junto al prompt.
- [ ] Se mide el coste en tokens por petición.

> Un prompt sin probar es un bug esperando a su usuario.
