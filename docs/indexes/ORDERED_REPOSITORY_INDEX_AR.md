# الفهرس المرتب — VX-runtime

تاريخ الجرد: 2026-10-21 (الرياض).

- المستودع: `fisallllll280-code/VX-runtime`.
- مصدر الجرد: شجرة Git الكاملة للالتزام `3f018339a38e324a5049b0caf6d4708290ec1255`؛ دون اقتطاع.
- المسؤولية: التنفيذ المحكوم وسياسات القدرات والأحداث وإعادة التشغيل.
- عدد الملفات قبل إضافة هذا الفهرس: **23**.
- الأصل: Derived / فهرس ملاحي مشتق من مسارات Git؛ لا يعيد ترقيم هويات Ω أو الفهرس التاريخي.
- الحالة: جرد ملفات مرصودة فقط؛ لا يثبت اجتياز الاختبارات أو التشغيل أو اعتماد المحتوى.

## 1. ترتيب القراءة والعمل

1. هوية المستودع وREADME وعقد المسؤولية إن وجد.
2. الفهارس والمواصفات والعقود والسياسات.
3. الشيفرة والموصلات والواجهات الموجودة.
4. الاختبارات وملفات CI والأدلة المسجلة؛ وجودها لا يثبت نجاحها.
5. التشغيل والاستعادة ثم مراجعة الأدلة والاعتماد.

## 2. حدود المسؤوليات بين المستودعات

| المستودع | المسؤولية | فهرسه في فرع المراجعة |
|---|---|---|
| VAIXLNS | المرجع المركزي للمعمارية والحوكمة والفهارس والاستعادة | [الفهرس](https://github.com/fisallllll280-code/VAIXLNS/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |
| VAIXLNS-unified | التنفيذ المتكامل؛ لا يمنح سلطة اعتماد مرجعي | [الفهرس](https://github.com/fisallllll280-code/VAIXLNS-unified/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |
| VX-runtime | التنفيذ المحكوم وسياسات القدرات والأحداث وإعادة التشغيل | [الفهرس](https://github.com/fisallllll280-code/VX-runtime/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |
| NEXENT | البحث والاكتشاف والتركيب ومقترحات المعمارية | [الفهرس](https://github.com/fisallllll280-code/NEXENT/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |
| NAXLNS | الهندسة وتحليل المستودعات ومرشحات التحقق | [الفهرس](https://github.com/fisallllll280-code/NAXLNS/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |
| vx-financial-kernel | النواة المالية والمحاكاة؛ الوصف لا يثبت تشغيلًا ماليًا | [الفهرس](https://github.com/fisallllll280-code/vx-financial-kernel/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |
| vx-agents-fabric | تنسيق الوكلاء المتخصصين وعقود الأدوات والمراجعة | [الفهرس](https://github.com/fisallllll280-code/vx-agents-fabric/blob/docs/ordered-repository-indexes-20261021/docs/indexes/ORDERED_REPOSITORY_INDEX_AR.md) |

VAIXLNS يحكم الاعتماد المرجعي. لا تثبت هذه الخريطة اتصالًا حيًا بين الأنظمة. تبقى مطابقة VLNS مع NAXLNS ومطابقة NEXNET مع NEXENT غير محسومتين وفق فهرس الاتحاد؛ لا إعادة تسمية أو دمج تلقائيًا.

## 3. ترتيب الفهارس الأصلي 00–27

الترتيب التالي من [تصنيف الفهرس الأصلي](https://github.com/fisallllll280-code/VAIXLNS/blob/6bd55a9b44696cc2c7746bc66e2d39f0f274a81f/registry/indexes/zero-loss-index-taxonomy.v1.json)؛ هو ترتيب مناظر الفهرس وليس أرقام بنود تاريخية.

| الترتيب | الفهرس | المفتاح الأصلي |
|---|---|---|
| 00 | المصادر | `source_index` |
| 01 | الفهرس التاريخي | `legacy_master_index` |
| 02 | الكيانات | `entity_index` |
| 03 | المصطلحات | `terminology_index` |
| 04 | الابتكارات | `innovation_index` |
| 05 | المعمارية | `architecture_index` |
| 06 | القدرات | `capability_index` |
| 07 | العقود | `contract_index` |
| 08 | الصلاحيات | `authority_index` |
| 09 | الأحداث | `event_index` |
| 10 | الحالات | `state_index` |
| 11 | الاعتماديات | `dependency_index` |
| 12 | العلاقات | `relation_index` |
| 13 | النسب والإصدارات التاريخية | `lineage_index` |
| 14 | المراجع المعتمدة | `canonical_index` |
| 15 | التنفيذ | `implementation_index` |
| 16 | المستودعات | `repository_index` |
| 17 | الملفات والمخرجات | `artifact_index` |
| 18 | الاختبارات | `test_index` |
| 19 | الأدلة | `evidence_index` |
| 20 | البراهين | `proof_index` |
| 21 | التشغيل | `operation_index` |
| 22 | الفشل والاستعادة | `failure_recovery_index` |
| 23 | الأمن | `security_index` |
| 24 | الرصد | `observability_index` |
| 25 | المحاكاة | `simulation_index` |
| 26 | التطور | `evolution_index` |
| 27 | الإحالات المتقاطعة | `cross_reference_index` |

## 4. جرد جميع الملفات بالترتيب

ترتيب ثابت بحسب المسار. الرقم هنا رقم عرض محلي فقط. البصمة **Git blob SHA-1** كما أعادتها واجهة Git وليست SHA-256 لبايتات الملف. روابط المصدر مثبتة على الالتزام أعلاه. لا يشمل الجرد فروعًا أخرى أو تاريخ Git الكامل أو ملفات خارج المستودع، ولا يشمل الفهرس الجديد نفسه.

| رقم العرض | الملف الأصلي | الحجم بالبايت | Git blob SHA-1 |
|---|---|---:|---|
| 0001 | [.github/workflows/vaixlns-conformance.yml](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/.github/workflows/vaixlns-conformance.yml) | 1453 | `95b24344eb96d7899b41f634dd5bdd96ac8f2644` |
| 0002 | [.gitignore](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/.gitignore) | 697 | `529fe7632257e5d536c98e1cfe8a0141177fdee1` |
| 0003 | [README.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/README.md) | 7561 | `6ec8af8c3724baac04f7eb4a9aa8974c765beced` |
| 0004 | [VAIXLNS_REPOSITORY_CONTRACT.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/VAIXLNS_REPOSITORY_CONTRACT.md) | 1211 | `fbe05b88f795894131267831445f005b5ed27919` |
| 0005 | [docs/FABLE5_DERIVED_INTEGRATION.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/FABLE5_DERIVED_INTEGRATION.md) | 8851 | `66b1be2386340e61206e035e92d31064074f2324` |
| 0006 | [docs/OMEGA_FABRIC_CONTRACT.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/OMEGA_FABRIC_CONTRACT.md) | 416 | `df66d971fd76712e319c45801fc3cf89c820d6c8` |
| 0007 | [docs/REPOSITORY_OPERATIONS.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/REPOSITORY_OPERATIONS.md) | 952 | `b9cab86052107b16a7e0c43757135249ad47c572` |
| 0008 | [docs/RIRF_EXECUTION_BOUNDARY_V1.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/RIRF_EXECUTION_BOUNDARY_V1.md) | 964 | `71a39c09d5ab6b6e55cfa2634117d0604e300728` |
| 0009 | [docs/VAIXLNS_FEDERATION_ROLE_V1.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/VAIXLNS_FEDERATION_ROLE_V1.md) | 740 | `96826ce25a0bb090c3c0a976ef225f1d4e4f7d7f` |
| 0010 | [docs/VAIXLNS_REPOSITORY_BOUNDARY.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/VAIXLNS_REPOSITORY_BOUNDARY.md) | 400 | `8aa9de527474e987f87854a2ba79cdbf10ca1fae` |
| 0011 | [docs/financial_agents/VX_AGENT_WORKSHOP_RUNTIME_CONTRACT_V1.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/financial_agents/VX_AGENT_WORKSHOP_RUNTIME_CONTRACT_V1.md) | 8844 | `02f1f8da868f6940b08d9b8f34d2b3b6f9f2e838` |
| 0012 | [docs/integration/ARC_X_BOUNDARY_V1.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/integration/ARC_X_BOUNDARY_V1.md) | 1063 | `b7d18a31249c5ec35012ca91a610dd889f8d22f3` |
| 0013 | [docs/manuals/00_STATUS_AR.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/manuals/00_STATUS_AR.md) | 292 | `d98d72e2b4d2a160b29144305f4d454ce573858f` |
| 0014 | [docs/manuals/01_ACTIVATION_AR.md](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/docs/manuals/01_ACTIVATION_AR.md) | 545 | `c5c458b88e55cd9e003a1565ca115d96b45aeff3` |
| 0015 | [tests/test_core.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/tests/test_core.py) | 3931 | `c3ed667634bc9eecea3e9273ec7c48e3f8fa8151` |
| 0016 | [tests/test_external_integration.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/tests/test_external_integration.py) | 1098 | `b19d4b6997263be0c95d92ef1703b1d566ef4442` |
| 0017 | [tests/test_finance.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/tests/test_finance.py) | 1182 | `77e8f07763fac487286eea2288eeeebb92356503` |
| 0018 | [tests/test_financial_agent_factory.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/tests/test_financial_agent_factory.py) | 6009 | `e1abcee92bba806d9a0efe12953177d6f39f9d9e` |
| 0019 | [vxruntime/__init__.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/vxruntime/__init__.py) | 463 | `51bffae21b033bd9f7677862f720bdf7a7f4beeb` |
| 0020 | [vxruntime/core.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/vxruntime/core.py) | 7733 | `13a8b2586c2cbddc83b8afbf9fda541481d65fba` |
| 0021 | [vxruntime/external_integration.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/vxruntime/external_integration.py) | 1492 | `ec06b1635b9776689fb82048115e185801997343` |
| 0022 | [vxruntime/finance.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/vxruntime/finance.py) | 3406 | `70a792a0937751787275908c4a486d3dd9d20545` |
| 0023 | [vxruntime/financial_agent_factory.py](https://github.com/fisallllll280-code/VX-runtime/blob/3f018339a38e324a5049b0caf6d4708290ec1255/vxruntime/financial_agent_factory.py) | 8604 | `ebb6965aa7f1ff5ce3335f7f657d4fcb2624aaa6` |

## 5. تحديث الفهرس والاستعادة

1. اقرأ عقود المستودع وأي AGENTS.md قبل التعديل، وثبّت التزام المصدر.
2. اجلب شجرة Git كاملة مع recursive=1 وارفض نتيجة truncated=true.
3. أعد الجرد بالمسار مع حجم كل ملف وبصمة blob، واحفظ مصدر كل سجل.
4. قارن الإضافات والتغييرات والحذف بالمصدر السابق؛ لا تحذف سجلًا تاريخيًا بصمت.
5. حافظ على أرقام الابتكارات الأصلية، وافصل رقم عرض الملفات عن legacy_id وcanonical_id.
6. احفظ التحديث في فرع مراجعة؛ لا دمج إلى main، ولا تعديل project.genome أو Ω.000 ضمن هذه المهمة.

## 6. الفجوات وحدود الإثبات

- الاستعادة الكاملة لبنود 0001–2750 غير مثبتة؛ لا تُنشأ بنود افتراضية لسد الأرقام.
- RECOVERED وCANONICAL وPROPOSED وIMPLEMENTED وVERIFIED حالات منفصلة؛ الجرد لا يرقّي أيًّا منها.
- فحص هذه المهمة يثبت مطابقة المسارات والبصمات لشجرة المصدر فقط؛ لا اختبارات تشغيلية نُفذت ضمن إنشاء هذا الملف.
