---
title: "بناء نظام RAG على Google Cloud"
description: "من استيعاب المستندات إلى وكيل في بيئة الإنتاج: Vertex AI RAG Engine وGemini وCloud Run."
cover: ./images/cover.svg
tags: [rag, gcp, vertex-ai, gemini, cloud-run]
level: intermediate
duration: 4h
date: 2026-09-01
updated: 2026-10-01
authors: [Youcef]
references:
  - title: awesome-llm-apps
    url: https://github.com/Shubhamsaboo/awesome-llm-apps
    note: "Collection d'applications LLM et de RAG open source"
  - title: GoogleCloudPlatform/generative-ai
    url: https://github.com/GoogleCloudPlatform/generative-ai
    note: Notebooks officiels Vertex AI et Gemini
  - title: "Vertex AI RAG Engine : vue d'ensemble"
    url: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview
  - title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)"
    url: https://arxiv.org/abs/2005.11401
    note: Article fondateur du RAG
---

يرشدك هذا المساق خطوة بخطوة إلى بناء نظام **توليد معزّز بالاسترجاع** (RAG) مستضاف بالكامل على Google Cloud.

## ما الذي ستبنيه

مساعد يجيب عن أسئلة فرقك اعتمادًا على الوثائق الداخلية، مع ذكر مصادره:

1. **مجموعة بيانات (corpus)** في Vertex AI RAG Engine تُغذّى من Cloud Storage؛
2. **مهمة مزامنة** على Cloud Run تعيد فهرسة المستندات المعدّلة؛
3. **وكيل ADK** منشور على Cloud Run يستعلم المجموعة ويستدعي Gemini.

## محتوى المساق

| الوحدة | المحتوى | المدة |
| --- | --- | --- |
| الأساسيات | بنية RAG، التضمينات، التشابه | ساعة ونصف |
| التطبيق | التثبيت، Terraform، النشر، الملخّص | ساعتان ونصف |

## المتطلبات المسبقة

- مشروع على Google Cloud مع تفعيل الفوترة.
- معرفة أساسية بلغة Python وسطر الأوامر.
