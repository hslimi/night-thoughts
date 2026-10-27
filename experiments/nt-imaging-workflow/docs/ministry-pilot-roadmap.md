# Ministry-facing governed pilot roadmap

This repository is a demonstrable technical foundation for a governed pilot, not a ministry-, hospital-, procurement-, or clinical-ready product.

1. **Governance and intended use.** Name accountable owners, users, scope, prohibited uses, human authority, escalation, and change control.
2. **Data protection and threat assessment.** Complete DPIA, data-flow inventory, residency/retention decisions, threat modeling, supplier review, and incident procedures.
3. **Standards-based imaging ingestion.** Validate DICOM confidentiality profiles, study/series handling, compressed syntaxes, overlays, and conformance independently. Consider MONAI Deploy for packaging and Orthanc for research PACS/DICOMweb only as later components.
4. **Representative retrospective evaluation.** Use authorized representative data and radiologist-designed clinical, safety, subgroup, and workflow endpoints with versioned provenance.
5. **Human factors.** Study comprehension, alert fatigue, automation bias, rejection/correction behavior, accessibility, training, and reviewer time.
6. **Interoperability.** Design DICOMweb/PACS, identity, audit, terminology, and workflow semantics. FHIR `DiagnosticReport` comes only after references, terminology, validation, and ownership are designed; no FHIR interoperability is claimed now.
7. **Institutional deployment.** Evaluate PostgreSQL, governed object storage, RBAC/SSO with institutional OIDC, retention, monitoring, backup, disaster recovery, and OpenTelemetry-compatible observability. Replace development auth and in-memory persistence.
8. **Prospective silent-mode pilot.** No clinical action from outputs; measure technical and workflow safety under approved governance.
9. **Independent review.** Clinical, security, privacy, legal, regulatory, accessibility, and operational assessment with documented remediation.
10. **Controlled go/no-go.** Defined thresholds, staged authorization, rollback, post-deployment monitoring, and periodic revalidation. Any stage can stop the programme.
