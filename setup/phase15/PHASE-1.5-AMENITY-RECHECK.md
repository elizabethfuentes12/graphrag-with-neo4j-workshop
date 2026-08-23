# Phase 1.5 amenity recheck

Checked offline against the committed 300-document corpus on 2026-08-23.

| Reference fact | Deterministic result |
|---|---:|
| Source documents | 300 |
| Amenity assertions | 1,632 |
| Distinct amenity names | 65 |
| Sources whose amenity list includes a pool | 175 |
| Chicago hotels | 2 |
| Chicago hotels with both spa and pool | 1 |
| Shared authored Chicago WiFi label | `Complimentary High-Speed Wifi` |

`setup/test_phase15_reference_facts.py` derives these values from
`notebooks/02-connected-context/hotel-faqs.zip`. It does not call Bedrock or
Neo4j.

The earlier Phase 1.5 reports remain historical evidence from the defective
292-Hotel graph. Their reported graph value of 168 pool-bearing Hotels should
not be rewritten. A graph and agent evaluation against the rebuilt artifact is
still required before release. The corrected graph reference is expected to be
175, but that value must come from the rebuilt graph rather than this source
check.
