---
usecases: [generation-contenu]
title: Checklist prompt engineering
description: Les vérifications à faire avant de mettre un prompt en production.
tags: [prompt, gemini, bonnes-pratiques]
level: beginner
date: 2026-09-15
---

Un bon prompt se relit comme une spécification. Avant de le livrer, passez cette liste.

## Contenu du prompt

- [ ] Le rôle et l'objectif sont énoncés dès la première phrase.
- [ ] Le public cible et le ton sont précisés.
- [ ] Le format de sortie est explicite (JSON, Markdown, longueur maximale).
- [ ] Deux ou trois exemples (*few-shot*) couvrent les cas typiques **et** un cas limite.
- [ ] Les contraintes négatives sont formulées positivement (« réponds en français » plutôt que « ne réponds pas en anglais »).

## Robustesse

- [ ] Les données utilisateur sont séparées des instructions (balises `<document>`, délimiteurs).
- [ ] Le modèle sait quoi répondre quand l'information manque.
- [ ] La température est adaptée : basse pour l'extraction, plus haute pour la créativité.
- [ ] Une sortie structurée est imposée via `response_schema` quand c'est possible.

## Évaluation

- [ ] Un jeu de 20 à 50 cas de test est versionné avec le prompt.
- [ ] Les résultats sont comparés à la version précédente avant chaque changement.
- [ ] Le coût en tokens par requête est mesuré.

> Un prompt non testé est un bug qui attend son utilisateur.
