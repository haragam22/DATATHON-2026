# Data Store Table/Column Reference — Phase 1

Console-only creation (no CLI/SDK DDL exists in Catalyst — verified against docs.catalyst.zoho.com). Build tables in this order (parents before children, so Foreign Key columns can target an existing parent table).

Every table auto-gets `ROWID` (BigInt, real PK), `CREATORID`, `CREATEDTIME`, `MODIFIEDTIME` — don't recreate these.

**PK convention**: schema.md's named IDs (`CaseMasterID`, `AccusedMasterID`, ...) are kept as plain `Int`/`BigInt` columns (mandatory, unique where they're the row's own ID) alongside Catalyst's real `ROWID` PK. All cross-table relationships use Catalyst's native `Foreign Key` column type, which targets the parent table's `ROWID` — not the named ID column. So every FK below is "Foreign Key → ParentTable(ROWID)"; the named ID columns are business-readable but not enforcement points.

**On Delete**: `Cascade` for tightly-owned child rows (e.g. Victim/Accused/ComplainantDetails under CaseMaster), `Null` for optional/reference links (e.g. CourtID on CaseMaster).

Type mapping from schema.md: VARCHAR (short codes/names) → `Var Char` (≤255); NVARCHAR(MAX)/long free text → `Text`; DATE → `Date`; DATETIME → `DateTime`; INT → `Int`; DECIMAL → `Double`; BIT → `Boolean`; big serials → `BigInt`.

---

## Part 1 — KSP-original (fixed structure, build first)

### 1. State
| Column | Type | Notes |
|---|---|---|
| StateID | Int | mandatory, unique |
| StateName | Var Char | mandatory |
| NationalityID | Int | plain field, no FK target table defined |
| Active | Boolean | |

### 2. District
| Column | Type | Notes |
|---|---|---|
| DistrictID | Int | mandatory, unique |
| DistrictName | Var Char | mandatory |
| StateID_FK | Foreign Key → State | On Delete: Null |
| Active | Boolean | |

### 3. UnitType
| Column | Type | Notes |
|---|---|---|
| UnitTypeID | Int | mandatory, unique |
| UnitTypeName | Var Char | |
| CityDistState | Var Char | |
| Hierarchy | Int | |
| Active | Boolean | |

### 4. Unit
| Column | Type | Notes |
|---|---|---|
| UnitID | Int | mandatory, unique |
| UnitName | Var Char | |
| TypeID_FK | Foreign Key → UnitType | On Delete: Null |
| ParentUnit | Foreign Key → Unit | confirmed working (self-referencing FK) as of Phase 1 build, verified via `iac:export` |
| NationalityID | Int | plain field |
| StateID_FK | Foreign Key → State | On Delete: Null |
| DistrictID_FK | Foreign Key → District | On Delete: Null |
| Active | Boolean | |

### 5. Rank
| Column | Type | Notes |
|---|---|---|
| RankID | Int | mandatory, unique |
| RankName | Var Char | |
| Hierarchy | Int | |
| Active | Boolean | |

### 6. Designation
| Column | Type | Notes |
|---|---|---|
| DesignationID | Int | mandatory, unique |
| DesignationName | Var Char | |
| Active | Boolean | |
| SortOrder | Int | |

### 7. Employee
| Column | Type | Notes |
|---|---|---|
| EmployeeID | Int | mandatory, unique |
| DistrictID_FK | Foreign Key → District | On Delete: Null |
| UnitID_FK | Foreign Key → Unit | On Delete: Null |
| RankID_FK | Foreign Key → Rank | On Delete: Null |
| DesignationID_FK | Foreign Key → Designation | On Delete: Null |
| KGID | Var Char | |
| FirstName | Var Char | |
| EmployeeDOB | Date | |
| GenderID | Int | lookup value, no separate table in schema.md |
| BloodGroupID | Int | lookup value |
| PhysicallyChallenged | Boolean | |
| AppointmentDate | Date | |

### 8. CaseCategory
| Column | Type | Notes |
|---|---|---|
| CaseCategoryID | Int | mandatory, unique |
| LookupValue | Var Char | FIR / UDR / PAR / etc. |

### 9. GravityOffence
| Column | Type | Notes |
|---|---|---|
| GravityOffenceID | Int | mandatory, unique |
| LookupValue | Var Char | Heinous / Non-Heinous |

### 10. CrimeHead
| Column | Type | Notes |
|---|---|---|
| CrimeHeadID | Int | mandatory, unique |
| CrimeGroupName | Var Char | |
| Active | Boolean | |

### 11. CrimeSubHead
| Column | Type | Notes |
|---|---|---|
| CrimeSubHeadID | Int | mandatory, unique |
| CrimeHeadID_FK | Foreign Key → CrimeHead | On Delete: Cascade |
| CrimeHeadName | Var Char | e.g. "Murder", "Robbery" |
| SeqID | Int | |

### 12. Act
| Column | Type | Notes |
|---|---|---|
| ActCode | Var Char | mandatory, unique — treat as the named PK field |
| ActDescription | Var Char | |
| ShortName | Var Char | IPC / BNS / NDPS |
| Active | Boolean | |

### 13. Section
| Column | Type | Notes |
|---|---|---|
| ActCode_FK | Foreign Key → Act | On Delete: Cascade |
| SectionCode | Var Char | mandatory |
| SectionDescription | Var Char | |
| Active | Boolean | |

**IPC/BNS rule**: populate Act with both `IPC` and `BNS` rows; Section rows for both codes; app-layer join logic picks the applicable Act based on `CaseMaster.CrimeRegisteredDate` vs 2024-07-01 — no schema change needed for this, it's a query-time rule.

### 14. CrimeHeadActSection
| Column | Type | Notes |
|---|---|---|
| CrimeHeadID_FK | Foreign Key → CrimeHead | On Delete: Cascade |
| ActCode_FK | Foreign Key → Act | On Delete: Cascade |
| SectionCode_FK | Foreign Key → Section | On Delete: Cascade |

### 15. CaseStatusMaster
| Column | Type | Notes |
|---|---|---|
| CaseStatusID | Int | mandatory, unique |
| CaseStatusName | Var Char | Under Investigation / Charge Sheeted / Closed |

### 16. Court
| Column | Type | Notes |
|---|---|---|
| CourtID | Int | mandatory, unique |
| CourtName | Var Char | |
| DistrictID_FK | Foreign Key → District | On Delete: Null |
| StateID_FK | Foreign Key → State | On Delete: Null |
| Active | Boolean | |

### 17. CasteMaster
| Column | Type | Notes |
|---|---|---|
| caste_master_id | Int | mandatory, unique |
| caste_master_name | Var Char | |

### 18. ReligionMaster
| Column | Type | Notes |
|---|---|---|
| ReligionID | Int | mandatory, unique |
| ReligionName | Var Char | |

### 19. OccupationMaster
| Column | Type | Notes |
|---|---|---|
| OccupationID | Int | mandatory, unique |
| OccupationName | Var Char | |

### 20. CaseMaster
| Column | Type | Notes |
|---|---|---|
| CaseMasterID | Int | mandatory, unique |
| CrimeNo | Var Char | 1-digit category+4-digit district+4-digit station+4-digit year+5-digit serial — validate via regex at insert time, not a DB constraint |
| CaseNo | Var Char | |
| CrimeRegisteredDate | Date | drives IPC/BNS selection |
| PolicePersonID_FK | Foreign Key → Employee | On Delete: Null |
| PoliceStationID_FK | Foreign Key → Unit | On Delete: Null |
| CaseCategoryID_FK | Foreign Key → CaseCategory | On Delete: Null |
| GravityOffenceID_FK | Foreign Key → GravityOffence | On Delete: Null |
| CrimeMajorHeadID_FK | Foreign Key → CrimeHead | On Delete: Null |
| CrimeMinorHeadID_FK | Foreign Key → CrimeSubHead | On Delete: Null |
| CaseStatusID_FK | Foreign Key → CaseStatusMaster | On Delete: Null |
| CourtID_FK | Foreign Key → Court | On Delete: Null |
| IncidentFromDate | DateTime | |
| IncidentToDate | DateTime | |
| InfoReceivedPSDate | DateTime | |
| latitude | Double | |
| longitude | Double | |
| BriefFacts | Text | |

### 21. Inv_OccuranceTime (we define — 1:1 with CaseMaster)
| Column | Type | Notes |
|---|---|---|
| OccuranceTimeID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade; enforce 1:1 in app code (Catalyst FK doesn't have a native uniqueness constraint on FK columns — mark IsUnique if the console exposes it) |
| DayOfWeek | Var Char | |
| TimeOfDayBucket | Var Char | Morning/Afternoon/Evening/Night |
| PlaceOfOccurrenceType | Var Char | |
| PlaceOfOccurrenceDescription | Var Char | |
| IsOutdoor | Boolean | |

### 22. ComplainantDetails
| Column | Type | Notes |
|---|---|---|
| ComplainantID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| ComplainantName | Var Char | |
| AgeYear | Int | |
| OccupationID_FK | Foreign Key → OccupationMaster | On Delete: Null |
| ReligionID_FK | Foreign Key → ReligionMaster | On Delete: Null |
| CasteID_FK | Foreign Key → CasteMaster | On Delete: Null |
| GenderID | Int | lookup value |

### 23. ActSectionAssociation
| Column | Type | Notes |
|---|---|---|
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| ActID_FK | Foreign Key → Act | On Delete: Null |
| SectionID_FK | Foreign Key → Section | On Delete: Null |
| ActOrderID | Int | |
| SectionOrderID | Int | |

### 24. Victim
| Column | Type | Notes |
|---|---|---|
| VictimMasterID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| VictimName | Var Char | |
| AgeYear | Int | |
| GenderID | Int | lookup value |
| VictimPolice | Boolean | |

### 25. Accused
| Column | Type | Notes |
|---|---|---|
| AccusedMasterID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| AccusedName | Var Char | |
| AgeYear | Int | |
| GenderID | Int | lookup value |
| PersonID | Var Char | display label A1, A2... |

### 26. ArrestSurrender
| Column | Type | Notes |
|---|---|---|
| ArrestSurrenderID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| ArrestSurrenderTypeID | Int | lookup value |
| ArrestSurrenderDate | Date | |
| ArrestSurrenderStateId_FK | Foreign Key → State | On Delete: Null |
| ArrestSurrenderDistrictId_FK | Foreign Key → District | On Delete: Null |
| PoliceStationID_FK | Foreign Key → Unit | On Delete: Null |
| IOID_FK | Foreign Key → Employee | On Delete: Null |
| CourtID_FK | Foreign Key → Court | On Delete: Null |
| AccusedMasterID_FK | Foreign Key → Accused | On Delete: Cascade |
| IsAccused | Boolean | |
| IsComplainantAccused | Boolean | |

### 27. inv_arrestsurrenderaccused (we define — junction, backbone of graph layer, validate carefully)
| Column | Type | Notes |
|---|---|---|
| ArrestSurrenderAccusedID | Int | mandatory, unique |
| ArrestSurrenderID_FK | Foreign Key → ArrestSurrender | On Delete: Cascade |
| AccusedMasterID_FK | Foreign Key → Accused | On Delete: Cascade |
| RoleInEvent | Var Char | Primary / Associate |
| CreatedDate | DateTime | |

### 28. ChargesheetDetails
| Column | Type | Notes |
|---|---|---|
| CSID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| csdate | DateTime | |
| cstype | Var Char | A/B/C |
| PolicePersonID_FK | Foreign Key → Employee | On Delete: Null |

---

## Part 2 — Financial Crime Module (Phase 19, Person A owns build — this spec still useful for reference)

### 29. Account
| Column | Type | Notes |
|---|---|---|
| AccountID | Int | mandatory, unique |
| AccountHolderName | Var Char | |
| BankName | Var Char | |
| AccountNumberMasked | Var Char | synthetic only |
| AccountType | Var Char | |
| Active | Boolean | |

### 30. Transaction
| Column | Type | Notes |
|---|---|---|
| TransactionID | Int | mandatory, unique |
| FromAccountID_FK | Foreign Key → Account | On Delete: Null |
| ToAccountID_FK | Foreign Key → Account | On Delete: Null |
| Amount | Double | |
| TransactionDate | DateTime | |
| TransactionType | Var Char | |
| Flagged | Boolean | |

### 31. AccountCaseLink
| Column | Type | Notes |
|---|---|---|
| LinkID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| AccountID_FK | Foreign Key → Account | On Delete: Cascade |
| RoleInCase | Var Char | |

---

## Part 3 — Conversation, RBAC, Risk Score, Evidence (ours)

### 32. AppRole
| Column | Type | Notes |
|---|---|---|
| RoleID | Int | mandatory, unique |
| RoleName | Var Char | Investigator/Analyst/Supervisor/Policymaker |

### 33. AppUser
| Column | Type | Notes |
|---|---|---|
| AppUserID | Int | mandatory, unique |
| CatalystAuthID | Var Char | from Catalyst Authentication |
| EmployeeID_FK | Foreign Key → Employee | On Delete: Null (nullable link) |
| RoleID_FK | Foreign Key → AppRole | On Delete: Null |

### 34. ConversationSession
| Column | Type | Notes |
|---|---|---|
| SessionID | Int | mandatory, unique |
| AppUserID_FK | Foreign Key → AppUser | On Delete: Cascade |
| StartedAt | DateTime | |
| EndedAt | DateTime | nullable |

### 35. ConversationMessage
| Column | Type | Notes |
|---|---|---|
| MessageID | Int | mandatory, unique |
| SessionID_FK | Foreign Key → ConversationSession | On Delete: Cascade |
| Role | Var Char | user / assistant |
| MessageText | Text | |
| GeneratedSQL | Text | assistant messages only |
| ConfidenceScore | Double | assistant messages only |
| CitedCaseMasterIDs | Var Char | comma-separated |
| CreatedAt | DateTime | |

### 36. AuditLog
| Column | Type | Notes |
|---|---|---|
| AuditLogID | Int | mandatory, unique |
| AppUserID_FK | Foreign Key → AppUser | On Delete: Null |
| QueryText | Text | |
| GeneratedSQL | Text | |
| Timestamp | DateTime | |
| ResultRowCount | Int | |

### 37. RiskScore
| Column | Type | Notes |
|---|---|---|
| RiskScoreID | Int | mandatory, unique |
| AccusedMasterID_FK | Foreign Key → Accused | On Delete: Cascade |
| RiskScoreValue | Double | |
| ComputedDate | DateTime | |
| ModelVersion | Var Char | |
| TopFeaturesJSON | Text | SHAP output |
| CounterfactualJSON | Text | |

### 38. Evidence
| Column | Type | Notes |
|---|---|---|
| EvidenceID | Int | mandatory, unique |
| CaseMasterID_FK | Foreign Key → CaseMaster | On Delete: Cascade |
| EvidenceType | Var Char | video/audio/image/document |
| FileURL | Var Char | Catalyst Stratus location |
| Description | Var Char | |
| UploadedDate | DateTime | |

---

## Not in Data Store — lives in Catalyst NoSQL

**Similar-Case Embeddings** (Phase 13): `CaseMasterID` (reference), `EmbeddingVector`, `EmbeddingModelVersion` — created via NoSQL table setup, not this Data Store DDL. See schema.md Part 3 for field list; NoSQL table creation mechanism to be verified when Phase 13 starts.

---

## As-built verification (Phase 1 complete, confirmed via `iac:export` 2026-07-20)
All 38 tables exist in Catalyst Data Store, matching this doc's table list exactly. Column-level naming drift (typos/renames introduced during console build) is logged in schema.md's "Naming drift" table — use the **Built as** names in all code, not the names in this doc's tables above.

All 56 FK columns verified pointed at correct parent tables (the `CaseStatusID_FK` → `CrimeSubHead` bug was fixed and reverified 2026-07-20, now correctly → `CaseStatusMaster`). `Unit.ParentUnit` self-FK confirmed working.

**Phase 1 status: complete.**
