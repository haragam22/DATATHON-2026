# Backend Database Schema — Consolidated Reference

This file consolidates everything from the original KSP ER diagram PDF, plus the tables we need to define ourselves (schema gaps) and the tables required by features we've added on top. This is the single reference for Phase 1 (Schema Finalization) — the PDF can stay in the repo as a source document, but this file is what gets built against.

## Naming drift — as-built in Catalyst Data Store (Phase 1, confirmed via `iac:export` 2026-07-20)
The columns below were built with a different spelling/name than this doc originally specified. Code, queries, and synthetic-data generation must use the **Built as** name, not the original.

| Table | Documented name | Built as |
|---|---|---|
| AuditLog | Timestamp | `Time_stamp` |
| CaseMaster | CaseMasterID | `CseMasterID` |
| CaseMaster | InfoReceivedPSDate | `InfoRecievedPSDate` |
| CaseMaster | latitude | `Latitude` |
| CaseMaster | longitude | `Longitude` |
| CaseMaster | GravityOffenceID (as FK column) | `GravityOffenceID` *(built without `_FK` suffix used elsewhere — still a working Foreign Key column)* |
| Court | Active | `Acitve` |
| Designation | DesignationName | `DesigationName` |
| GravityOffence | GravityOffenceID | `GravityOffence` *(same name as the table)* |
| OccupationMaster | OccupationName | `OccupationMater` |
| Inv_OccuranceTime | PlaceOfOccurrenceDescription | `PlaceOfOccuranceDescription` |
| Inv_OccuranceTime | PlaceOfOccurrenceType | `PlaceOfOccuranceType` |

~~**Known bug**: `CaseMaster.CaseStatusID_FK` was built pointing at `CrimeSubHead` instead of `CaseStatusMaster`.~~ Fixed and reverified 2026-07-20 — now correctly points at `CaseStatusMaster`.

## ON DELETE CASCADE — confirmed firing for real (2026-07-22)
`ddl_reference.md` already *declares* `Cascade` on `ArrestSurrender.AccusedMasterID_FK`, `RiskScore.AccusedMasterID_FK`, and both `inv_arrestsurrenderaccused` FKs (all → `Accused`) — this was an intentional Phase 1 design choice, not a Catalyst default. What was NOT previously confirmed: whether Catalyst's console-built FK columns actually *enforce* that cascade at delete time, versus it being a declared-but-unverified intent.

Confirmed for real during a Phase 3 data-quality fix: deleting all rows from `Accused` via a ZCQL `DELETE FROM Accused WHERE ...` (through the Data Store REST API — the CLI has no delete command) automatically cascaded and emptied `ArrestSurrender`, `inv_arrestsurrenderaccused`, and `RiskScore` with no separate delete needed. Reproduced twice.

**Implication for anyone touching `Accused` going forward** (including via console): deleting an Accused row silently deletes its ArrestSurrender/RiskScore/inv_arrestsurrenderaccused rows too. There is no soft-delete or archival step — if you're removing a bad test row rather than doing a full data reset, back up first.

---

## Part 1 — Original KSP-provided schema

### CaseMaster
| Column | Type | Key | Description |
|---|---|---|---|
| CaseMasterID | INT | PK | Unique identifier for each FIR/case |
| CrimeNo | VARCHAR | | 1-digit Case Category Code + 4-digit District ID + 4-digit Police Station ID + 4-digit Year + 5-digit running serial |
| CaseNo | VARCHAR | | YYYY + 5-digit running serial (last 9 digits of CrimeNo) |
| CrimeRegisteredDate | DATE | | Date FIR was registered |
| PolicePersonID | INT | FK → Employee.EmployeeID | Officer who registered the FIR |
| PoliceStationID | INT | FK → Unit.UnitID | Police station where FIR is registered |
| CaseCategoryID | INT | FK → CaseCategory.CaseCategoryID | Category (FIR, UDR, PAR, Zero FIR) |
| GravityOffenceID | INT | FK → GravityOffence.GravityOffenceID | Gravity level |
| CrimeMajorHeadID | INT | FK → CrimeHead.CrimeHeadID | Major crime head |
| CrimeMinorHeadID | INT | FK → CrimeSubHead.CrimeSubHeadID | Minor crime sub-head |
| CaseStatusID | INT | FK → CaseStatusMaster.CaseStatusID | Current case status |
| CourtID | INT | FK → Court.CourtID | Court hearing the case |
| IncidentFromDate | DATETIME | | Incident start |
| IncidentToDate | DATETIME | | Incident end |
| InfoReceivedPSDate | DATETIME | | When station received info |
| latitude | DECIMAL | | Incident latitude |
| longitude | DECIMAL | | Incident longitude |
| BriefFacts | NVARCHAR(MAX) | | Case summary |

### ComplainantDetails
| Column | Type | Key | Description |
|---|---|---|---|
| ComplainantID | INT | PK | Unique complainant ID |
| CaseMasterID | INT | FK → CaseMaster | FIR this complainant filed |
| ComplainantName | VARCHAR | | Full name |
| AgeYear | INT | | Age |
| OccupationID | INT | FK → OccupationMaster | Occupation |
| ReligionID | INT | FK → ReligionMaster | Religion |
| CasteID | INT | FK → CasteMaster.caste_master_id | Caste |
| GenderID | INT | | Gender (lookup) |

### ActSectionAssociation
| Column | Type | Key | Description |
|---|---|---|---|
| CaseMasterID | INT | FK → CaseMaster | FIR this applies to |
| ActID | INT | FK → Act.ActCode | Legal act invoked |
| SectionID | INT | FK → Section.SectionCode | Section invoked |
| ActOrderID | INT | | Display order of act |
| SectionOrderID | INT | | Display order of section |

### Victim
| Column | Type | Key | Description |
|---|---|---|---|
| VictimMasterID | INT | PK | Unique victim ID |
| CaseMasterID | INT | FK → CaseMaster | FIR this victim belongs to |
| VictimName | VARCHAR | | Full name |
| AgeYear | INT | | Age |
| GenderID | INT | | Gender (M/F/T lookup) |
| VictimPolice | VARCHAR | | 1 if victim is police, else 0 |

### Accused
| Column | Type | Key | Description |
|---|---|---|---|
| AccusedMasterID | INT | PK | Unique accused ID |
| CaseMasterID | INT | FK → CaseMaster | FIR this accused is linked to |
| AccusedName | VARCHAR | | Full name |
| AgeYear | INT | | Age |
| GenderID | INT | | Gender (M/F/T) |
| PersonID | VARCHAR | | Sorting label (A1, A2, A3...) |

### ArrestSurrender
| Column | Type | Key | Description |
|---|---|---|---|
| ArrestSurrenderID | INT | PK | Unique event ID |
| CaseMasterID | INT | FK → CaseMaster | Linked FIR |
| ArrestSurrenderTypeID | INT | | Arrest or voluntary surrender (lookup) |
| ArrestSurrenderDate | DATE | | Event date |
| ArrestSurrenderStateId | INT | FK → State | State of event |
| ArrestSurrenderDistrictId | INT | FK → District | District of event |
| PoliceStationID | INT | FK → Unit.UnitID | Station handling arrest |
| IOID | INT | FK → Employee.EmployeeID | Investigating officer |
| CourtID | INT | FK → Court | Court accused was produced before |
| AccusedMasterID | INT | FK → Accused | Linked accused |
| IsAccused | BIT | | Whether primary accused |
| IsComplainantAccused | BIT | | Whether complainant is also accused |

### Act
| Column | Type | Key | Description |
|---|---|---|---|
| ActCode | VARCHAR | PK | Unique code (IPC, BNS, NDPS, etc.) |
| ActDescription | VARCHAR | | Full name |
| ShortName | VARCHAR | | Abbreviation |
| Active | BIT | | 1=Active, 0=Inactive |

### Section
| Column | Type | Key | Description |
|---|---|---|---|
| ActCode | VARCHAR | FK → Act | Parent act |
| SectionCode | VARCHAR | | Section number |
| SectionDescription | VARCHAR | | Full description |
| Active | BIT | | 1=Active, 0=Inactive |

### CrimeHeadActSection
| Column | Type | Key | Description |
|---|---|---|---|
| CrimeHeadID | INT | FK → CrimeHead | Crime head this maps to |
| ActCode | VARCHAR | FK → Act | Linked act |
| SectionCode | VARCHAR | FK → Section | Linked section |

### CrimeHead
| Column | Type | Key | Description |
|---|---|---|---|
| CrimeHeadID | INT | PK | Major crime head ID |
| CrimeGroupName | VARCHAR | | e.g. "Crimes Against Body" |
| Active | BIT | | 1=Active, 0=Inactive |

### CrimeSubHead
| Column | Type | Key | Description |
|---|---|---|---|
| CrimeSubHeadID | INT | PK | Sub-head ID |
| CrimeHeadID | INT | FK → CrimeHead | Parent major head |
| CrimeHeadName | VARCHAR | | e.g. "Murder", "Robbery" |
| SeqID | INT | | Display sort order |

### CasteMaster
| Column | Type | Key | Description |
|---|---|---|---|
| caste_master_id | INT | PK | Unique caste ID |
| caste_master_name | VARCHAR | | Caste name |

### ReligionMaster
| Column | Type | Key | Description |
|---|---|---|---|
| ReligionID | INT | PK | Unique religion ID |
| ReligionName | VARCHAR | | e.g. Hindu, Muslim, Christian |

### OccupationMaster
| Column | Type | Key | Description |
|---|---|---|---|
| OccupationID | INT | PK | Unique occupation ID |
| OccupationName | VARCHAR | | e.g. Farmer, Government Employee |

### CaseStatusMaster
| Column | Type | Key | Description |
|---|---|---|---|
| CaseStatusID | INT | PK | Unique status ID |
| CaseStatusName | VARCHAR | | e.g. Under Investigation, Charge Sheeted, Closed |

### Court
| Column | Type | Key | Description |
|---|---|---|---|
| CourtID | INT | PK | Unique court ID |
| CourtName | VARCHAR | | Full name |
| DistrictID | INT | FK → District | District located in |
| StateID | INT | FK → State | State located in |
| Active | BIT | | 1=Active, 0=Inactive |

### District
| Column | Type | Key | Description |
|---|---|---|---|
| DistrictID | INT | PK | Unique district ID |
| DistrictName | VARCHAR | | Name |
| StateID | INT | FK → State | Parent state |
| Active | BIT | | 1=Active, 0=Inactive |

### State
| Column | Type | Key | Description |
|---|---|---|---|
| StateID | INT | PK | Unique state ID |
| StateName | VARCHAR | | Name |
| NationalityID | INT | | Nationality reference |
| Active | BIT | | 1=Active, 0=Inactive |

### Unit
| Column | Type | Key | Description |
|---|---|---|---|
| UnitID | INT | PK | Unique unit ID |
| UnitName | VARCHAR | | Unit/station name |
| TypeID | INT | FK → UnitType | Type of unit |
| ParentUnit | INT | | Self-reference to UnitID for hierarchy |
| NationalityID | INT | | Nationality reference |
| StateID | INT | FK → State | State |
| DistrictID | INT | FK → District | District |
| Active | BIT | | 1=Active, 0=Inactive |

### UnitType
| Column | Type | Key | Description |
|---|---|---|---|
| UnitTypeID | INT | PK | Unique type ID |
| UnitTypeName | VARCHAR | | e.g. Police Station, Circle Office |
| CityDistState | VARCHAR | | Operational level |
| Hierarchy | INT | | Level number, lower = higher authority |
| Active | BIT | | 1=Active, 0=Inactive |

### Rank
| Column | Type | Key | Description |
|---|---|---|---|
| RankID | INT | PK | Unique rank ID |
| RankName | VARCHAR | | e.g. Constable, Inspector, DSP |
| Hierarchy | INT | | Level, lower = higher rank |
| Active | BIT | | 1=Active, 0=Inactive |

### Designation
| Column | Type | Key | Description |
|---|---|---|---|
| DesignationID | INT | PK | Unique designation ID |
| DesignationName | VARCHAR | | e.g. Investigating Officer, SHO |
| Active | BIT | | 1=Active, 0=Inactive |
| SortOrder | INT | | Display order |

### Employee
| Column | Type | Key | Description |
|---|---|---|---|
| EmployeeID | INT | PK | Unique employee ID |
| DistrictID | INT | FK → District | Current posting district |
| UnitID | INT | FK → Unit | Assigned unit |
| RankID | INT | FK → Rank | Current rank |
| DesignationID | INT | FK → Designation | Current designation |
| KGID | VARCHAR | | Karnataka Government ID |
| FirstName | VARCHAR | | First name |
| EmployeeDOB | DATE | | Date of birth |
| GenderID | INT | | Gender (lookup) |
| BloodGroupID | INT | | Blood group (lookup) |
| PhysicallyChallenged | BIT | | 1=Yes, 0=No |
| AppointmentDate | DATE | | Date of appointment |

### CaseCategory
| Column | Type | Key | Description |
|---|---|---|---|
| CaseCategoryID | INT | PK | Unique category ID |
| LookupValue | VARCHAR | | FIR, UDR, PAR, etc. |

### GravityOffence
| Column | Type | Key | Description |
|---|---|---|---|
| GravityOffenceID | INT | PK | Unique gravity ID |
| LookupValue | VARCHAR | | e.g. Heinous, Non-Heinous |

### ChargesheetDetails
| Column | Type | Key | Description |
|---|---|---|---|
| CSID | INT | PK | Unique chargesheet ID |
| CaseMasterID | INT | FK → CaseMaster | Linked FIR |
| csdate | DATETIME | | Chargesheeted date |
| cstype | CHAR | | A=Chargesheet, B=False Case, C=Undetected |
| PolicePersonID | INT | FK → Employee.EmployeeID | Filing officer |

### Relationship Matrix (summary)
- CaseMaster → (1:many) Victim, Accused, ArrestSurrender, ComplainantDetails, ActSectionAssociation
- CaseMaster → (1:1) Inv_OccuranceTime
- CaseMaster → (many:1) CaseCategory, GravityOffence, CrimeHead, CrimeSubHead, CaseStatusMaster, Court, Employee
- ArrestSurrender → (1:many, via junction) inv_arrestsurrenderaccused → Accused
- ArrestSurrender → (many:1) State, District, Court, Employee (IOID)
- ComplainantDetails → (many:1) OccupationMaster, ReligionMaster, CasteMaster
- ActSectionAssociation → (many:1) Act, Section
- CrimeSubHead → (many:1) CrimeHead; CrimeHead → (1:many) CrimeHeadActSection; Act → (1:many) CrimeHeadActSection, Section
- Court, Unit, Employee → (many:1) District → (many:1) State

---

## Part 2 — Tables referenced but undefined in the original PDF (must build ourselves)

### Inv_OccuranceTime
Referenced as 1:1 with CaseMaster but never defined. Proposed columns:
| Column | Type | Key | Description |
|---|---|---|---|
| OccuranceTimeID | INT | PK | Unique ID |
| CaseMasterID | INT | FK → CaseMaster (unique) | The FIR this belongs to |
| DayOfWeek | VARCHAR | | Day of incident |
| TimeOfDayBucket | VARCHAR | | Morning/Afternoon/Evening/Night |
| PlaceOfOccurrenceType | VARCHAR | | e.g. Residence, Public Road, Commercial Establishment |
| PlaceOfOccurrenceDescription | VARCHAR | | Free-text landmark/description |
| IsOutdoor | BIT | | 1=Outdoor, 0=Indoor |

### inv_arrestsurrenderaccused
Junction table for the ArrestSurrender ↔ Accused many-to-many. Proposed columns:
| Column | Type | Key | Description |
|---|---|---|---|
| ArrestSurrenderAccusedID | INT | PK | Unique ID |
| ArrestSurrenderID | INT | FK → ArrestSurrender | Arrest/surrender event |
| AccusedMasterID | INT | FK → Accused | Accused linked to this event |
| RoleInEvent | VARCHAR | | e.g. Primary, Associate |
| CreatedDate | DATETIME | | Record creation timestamp |

This is the core table the network/graph analysis layer (Phase 9) builds on — get it right early.

---

## Part 3 — New tables required by features we've added

### Financial Crime Module (minimal, Phase 15)
**Account**
| Column | Type | Key | Description |
|---|---|---|---|
| AccountID | INT | PK | Unique account ID |
| AccountHolderName | VARCHAR | | Name on account |
| BankName | VARCHAR | | Bank |
| AccountNumberMasked | VARCHAR | | Masked account number (synthetic, never real) |
| AccountType | VARCHAR | | Savings/Current/etc. |
| Active | BIT | | 1=Active, 0=Inactive |

**Transaction**
| Column | Type | Key | Description |
|---|---|---|---|
| TransactionID | INT | PK | Unique transaction ID |
| FromAccountID | INT | FK → Account | Source account |
| ToAccountID | INT | FK → Account | Destination account |
| Amount | DECIMAL | | Transaction amount |
| TransactionDate | DATETIME | | Date/time of transaction |
| TransactionType | VARCHAR | | Transfer/Withdrawal/Deposit |
| Flagged | BIT | | 1 if flagged as suspicious |

**AccountCaseLink**
| Column | Type | Key | Description |
|---|---|---|---|
| LinkID | INT | PK | Unique link ID |
| CaseMasterID | INT | FK → CaseMaster | Linked FIR |
| AccountID | INT | FK → Account | Linked account |
| RoleInCase | VARCHAR | | e.g. Accused-owned, Victim-owned, Suspicious-third-party |

### Conversation & Context Retention (Phase 5, 16)
Needed for multi-turn context-aware chat and PDF export of conversation history — not covered anywhere in the original schema.

**ConversationSession**
| Column | Type | Key | Description |
|---|---|---|---|
| SessionID | INT | PK | Unique session ID |
| AppUserID | INT | FK → AppUser | User who owns this session |
| StartedAt | DATETIME | | Session start |
| EndedAt | DATETIME | | Session end (nullable) |

**ConversationMessage**
| Column | Type | Key | Description |
|---|---|---|---|
| MessageID | INT | PK | Unique message ID |
| SessionID | INT | FK → ConversationSession | Parent session |
| Role | VARCHAR | | "user" or "assistant" |
| MessageText | NVARCHAR(MAX) | | Message content |
| GeneratedSQL | NVARCHAR(MAX) | | SQL generated for this turn (assistant messages only) |
| ConfidenceScore | DECIMAL | | Self-consistency/verifier confidence (assistant messages only) |
| CitedCaseMasterIDs | VARCHAR | | Comma-separated case IDs cited in the answer |
| CreatedAt | DATETIME | | Timestamp |

### RBAC & Governance (Phase 13)
Catalyst Authentication handles identity, but we need an app-level layer mapping identities to KSP roles and scope.

**AppRole**
| Column | Type | Key | Description |
|---|---|---|---|
| RoleID | INT | PK | Unique role ID |
| RoleName | VARCHAR | | Investigator / Analyst / Supervisor / Policymaker |

**AppUser**
| Column | Type | Key | Description |
|---|---|---|---|
| AppUserID | INT | PK | Unique app user ID |
| CatalystAuthID | VARCHAR | | ID from Catalyst Authentication |
| EmployeeID | INT | FK → Employee (nullable) | Linked KSP employee record, if applicable |
| RoleID | INT | FK → AppRole | Assigned role |

**AuditLog**
| Column | Type | Key | Description |
|---|---|---|---|
| AuditLogID | INT | PK | Unique log entry ID |
| AppUserID | INT | FK → AppUser | Who ran the query |
| QueryText | NVARCHAR(MAX) | | Original NL question |
| GeneratedSQL | NVARCHAR(MAX) | | SQL that was executed |
| Timestamp | DATETIME | | When it ran |
| ResultRowCount | INT | | Rows returned |

### Offender Risk Scoring (Phase 11)
**RiskScore**
| Column | Type | Key | Description |
|---|---|---|---|
| RiskScoreID | INT | PK | Unique score record ID |
| AccusedMasterID | INT | FK → Accused | Accused this score belongs to |
| RiskScoreValue | DECIMAL | | Computed risk score |
| ComputedDate | DATETIME | | When it was computed |
| ModelVersion | VARCHAR | | Model version tag |
| TopFeaturesJSON | NVARCHAR(MAX) | | SHAP top-feature output |
| CounterfactualJSON | NVARCHAR(MAX) | | Counterfactual explanation output |

### Evidence Linking (video/audio/document artifacts)
Synthetic data has no real crime scene content — this table demonstrates the *retrieval and linking capability*, backed by placeholder/stock files in Catalyst Stratus, not real forensic evidence.
| Column | Type | Key | Description |
|---|---|---|---|
| EvidenceID | INT | PK | Unique evidence record ID |
| CaseMasterID | INT | FK → CaseMaster | Linked FIR |
| EvidenceType | VARCHAR | | video / audio / image / document |
| FileURL | VARCHAR | | Location in Catalyst Stratus |
| Description | VARCHAR | | Short description of the artifact |
| UploadedDate | DATETIME | | When it was added |

### Similar-Case Retrieval (Phase 13)
Lives in Catalyst NoSQL, not the relational store — documented here for completeness:
| Field | Description |
|---|---|
| CaseMasterID | Reference to the relational CaseMaster row |
| EmbeddingVector | Vector embedding of BriefFacts + structured MO features |
| EmbeddingModelVersion | Model version tag, for re-embedding if the model changes |

---

## Notes / things to watch
- **Act/Section master data must carry both IPC (pre-1 July 2024) and BNS (1 July 2024 onward)**, keyed off `CaseMaster.CrimeRegisteredDate`. Don't let synthetic generation default to IPC-only.
- **CasteID/ReligionID in ComplainantDetails** should be sampled independently of crime outcome during synthetic generation unless there's an explicit, documented reason not to — avoids the system "discovering" a spurious correlation that was actually engineered in by careless generation.
- **inv_arrestsurrenderaccused** is the single most important table for the network/graph layer — validate it thoroughly before Phase 9 starts.
- All financial crime, conversation, RBAC, and risk-score tables above are **proposed by us**, not KSP-specified — reasonable to adjust column names/types as implementation reveals better choices, unlike the Part 1 tables which are fixed by the original spec.
- **The Evidence table stores placeholder/stock files only.** There is no real crime scene content in a synthetic dataset — the feature demonstrates retrieval and linking, not real forensic analysis.
- **The investigation-board network visualization uses generic avatar icons, never real or fake photorealistic photos** of synthetic people — there's no real photo data to draw from, and generating convincing fake "booking photos" of nonexistent people is a credibility risk in front of a police jury, not a feature.
