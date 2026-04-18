# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[Major.Minor.Patch] - YYYY-MM-DD (Channels Released)
Channels : `Hotfix` (Over The Air), `App-Store`,  `Play-Store`
Examples:
    ## [x.y.z] - 2025-10-15 (OTA / App Store)

---


## [Unreleased]

### Changed
- Create an `common.App` and `common.Release` models where `min_version` is a FK to self, ensuring with constraint check that `min_version.version` is lower to the instannce version.
- Move the `App` and `Release` models from the `app` app to the `common` app and renamed to `App` and `Release` to keep the two table close to each other for better management.
- 

- modify the `app.Release` model `min_version` field from a 



---

## 2026.01.10+2

## Major
--
## Minor
- Implemented a management command to deploy the update code to the 
registed remote Django nodes.
---
## Patch


## 1.2.0 05-09-25
- the customer `fcm` is moved to the customer's token table : token.fcm
- We enable multi logn per customer per device(uuid)



## 1.1.1  20-08-25
- Fix customer kitchen catalog view by replacing in the queryset filter `profile` by `business`. As well we replace the in KitchenShift queryset filter `branch` by `kitchen`.
- Replace all KitchenItem 's `is_visible` by `is_active`


-----

## 1.1.0

- Add `is_phone_veified` and `is_email_verified` to the `BaseUser` model
- Manager can now signin only if their phone number is verified.
- Set `is_phone_verified` to `True` when the OTP is successfully verified/

---

## v1.0.1 
*2025-02-21*
- Added to the kitchen `deleted_at` field. To helps determine how long a kitchen has been deleted. It Can be used for automatic cleanup after a retention period. Useful for audits, disputes, and legal compliance.
- Add to the kitchen a `is_deleted` flag instead of is deleted. This allow us to used `is_active` when a kitchen temporarily stops operations (e.g., renovations, compliance issues). The kitchen can be reactivate the kitchen later
- For hierachic purpose add to the kitchen manager a kitchen field. In that case if the kitchen is clean automatically the manager will be deleted. This is mainly for conveniency using admin pannel.

- Made customer catalog more efficient:
    - improve is_nearby annotation using subquery. This in the previous method was returning 18 branches one for each branches event though i had only 4. The new approach result to only 4 branches.
    - Improve is_open annotation using suquery, laveraging postgis
    - Improve distinc by kitchen, by using windwo and RowNumber function


