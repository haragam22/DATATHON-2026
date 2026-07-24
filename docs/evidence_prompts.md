# Evidence Image Prompts (synthetic dataset, 10 cases)

Non-photorealistic, abstract only — no people, no faces, no realistic crime-scene
reconstruction. Per `docs/CLAUDE.md`: evidence is placeholder/stock content only,
never implying real forensic content. Every prompt below is deliberately styled as
an *evidence-tag / document-scan / object-close-up*, not a scene photo.

Two cases (CaseMasterID 17, 25) are the NDPS/drug-flavored pair, standing in for
the "multi-accused / gang" request — treated as a labeling choice for this demo,
not a DB-verified accused count (see note at bottom).

Naming convention for saved files: `evidence_{CaseMasterID}_{n}.png`.

---

## Case 17 — NDPS, Raichur (CrimeNo 200230092202400002)
> Complainant reported NDPS at Public Road in Raichur jurisdiction. UDR registered; investigation taken up.

**Prompt (document scan):**
"Flat-lay scan of a plain paper police evidence tag, printed label reading 'EXHIBIT A — CASE 200230092202400002', placed on a neutral gray background, slight paper texture and scanner shadow, no people, no logos, minimal graphic design style, not photorealistic."

**Prompt (object close-up):**
"Macro close-up of a small unmarked plastic sample pouch on a plain white surface, sealed with a red tamper tape, stylized flat illustration, muted colors, abstract icon-like rendering, no branding, no readable substance, not photographic."

---

## Case 25 — NDPS, Udupi (CrimeNo 400270105202500001)
> Incident of NDPS reported at Commercial Establishment, Udupi. Statements recorded; investigation in progress.

**Prompt (document scan):**
"Scanned image of a generic handwritten evidence log sheet, ruled lines, illegible scribbled placeholder text, coffee-stain corner, top-down flat scan look, monochrome, no real text, not photorealistic."

**Prompt (evidence-tag close-up):**
"Illustrated close-up of a numbered evidence tag (tag reads 'EXH-25') tied with string to a blurred indistinct object silhouette, flat vector/illustration style, desaturated palette, no facial features or people, abstract shapes only."

---

## Case 1 — Rape, Ballari (CrimeNo 200020007202300001)
> UDR registered; investigation taken up by the local police station.

**Prompt (document scan):**
"Top-down scan of a blank FIR-style form template, generic Kannada Police letterhead placeholder blocked out as gray bars, ruled fields, no real names or text, flat scanner aesthetic, not photographic."

---

## Case 252 — Cruelty by Husband, Bengaluru Rural (CrimeNo 500040013202400004)
> MVC registered.

**Prompt (object close-up):**
"Illustrated close-up of a torn fabric swatch in an evidence bag, flat matte lighting, muted earth tones, stylized icon rendering, no people, no scene context, abstract composition."

---

## Case 501 — Theft, Yadgir (CrimeNo 300300117202400007)
> Statements of complainant and witnesses recorded.

**Prompt (object close-up):**
"Flat illustration of a broken padlock resting on a plain gray surface, single soft studio-style shadow, minimalist icon-like rendering, no branding, no people, not photorealistic."

---

## Case 750 — Online Fraud, Chikballapur (CrimeNo 300080031202400012)
> Preliminary inquiry conducted.

**Prompt (document scan):**
"Abstract flat-design screenshot mockup of a generic banking transaction log with all values replaced by placeholder 'XXXX' blocks, neutral UI chrome, no real logos or numbers, not photographic."

---

## Case 999 — Molestation, Shivamogga (CrimeNo 100250099202400018)
> Preliminary inquiry conducted.

**Prompt (document scan):**
"Scanned generic complaint-register page, ruled table with blanked-out placeholder rows, slight paper grain, flat top-down scan look, no real text, not photorealistic."

---

## Case 1248 — Forgery, Chikballapur (CrimeNo 100080031202600007)
> FIR registered; investigation taken up.

**Prompt (document scan):**
"Illustrated close-up of a stamped document corner, generic round rubber-stamp shape (no readable text), aged paper texture, flat scan aesthetic, no signatures, not photographic."

---

## Case 1497 — Child Labour, Dharwad (CrimeNo 100130052202400019)
> FIR registered; investigation taken up.

**Prompt (object close-up):**
"Flat illustrated close-up of a generic tool/equipment silhouette (unspecified, non-identifying) on a plain workshop-style background, muted colors, icon-like abstract rendering, no people, not photorealistic."

---

## Case 1746 — Identity Theft, Udupi (CrimeNo 300270107202500015)
> Preliminary inquiry conducted.

**Prompt (document scan):**
"Abstract flat mockup of a blanked-out ID card template, placeholder gray bars instead of photo/name/number fields, minimal card-design illustration, no real identity fields, not photographic."

---

## Notes
- Source: `data_generation/csv_out/CaseMaster.csv` (this generation run), matched by BriefFacts keyword for the NDPS pair, sampled for variety otherwise.
- Accused-count per case couldn't be resolved from local pre-import CSVs (`Accused.CaseMasterID_FK` stores a post-import ROWID, not the local `CseMasterID` — only resolvable from the live Data Store, not these files). Cases 17/25 are the drug-flavored pair standing in for "multi-accused/gang" per your request, not a verified multi-accused pair.
- After generating: save files, upload via the Streamlit harness's new "Add Evidence" tab (`CaseMasterID` field = the number in each heading above).
