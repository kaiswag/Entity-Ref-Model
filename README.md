# Entity Ref Model

> [!WARNING]
> **This is NOT an official Shopware repository.**
> It is a private side project. It is not maintained, reviewed or supported by shopware AG,
> and nothing in here is an official statement about how Shopware works or should be used.
> Use it at your own risk.

A dependency map of all Shopware 6 entities. It tells you which entities reference which, which of those references are mandatory, and in which order data has to be loaded so every reference already has a target.

**Download and Open `index.html` in a browser.** It is a single self-contained file, no build step and no server needed. The rest of the files are for building new plans.

## What's in the page

- **Load plan:** all entities grouped into 18 packages, in an order where no mandatory reference points to a later package. Select a package to see what it needs directly, what it needs indirectly (because a predecessor needs it), and the concrete foreign-key chain behind each dependency.
- **Matrix:** package × package. Mandatory references all sit below the diagonal; whatever shows up above it is an optional back-reference that needs a second pass.
- **Entity lookup:** searchable list of all entities. For each one: every field with type, PK/FK, flags (required, translatable, inherited, write-protected, delete behaviour, …) and description, plus everything that must be loaded before it and everything that references it.
- **Special cases:** mutual mandatory references (must be written in one request), references to later packages (second pass via PATCH), and IDs stored inside JSON fields that Shopware does not validate.

The UI text is in German.

## What you can use it for

- **Data migration and account loading:** plan import order, split a migration into packages, and know up front which fields need a second pass or a combined write.
- **Analysis:** understand what depends on what before you delete, move or clean up data. For example: why a product cannot be deleted, or what breaks when a sales channel goes away.
- **Development:** look up fields, foreign keys and delete behaviour of an entity without digging through definitions; check what a plugin's entities hook into.
- **Demo and test setups:** build reproducible seed scripts that write data in a valid order.

## Scope of the included snapshot

The included `entity-schema.json` comes from a **Shopware 6.7.13.0** instance with everything Shopware ships itself (core, Commercial features such as B2B, Multi-Warehouse, CMS extensions, Digital Sales Rooms, Spatial, Advanced Search, subscriptions, and first-party plugins such as Custom Products and PayPal), **without third-party plugins**.

- **Smaller setups are covered.** If a project lacks some features or plugins, entities simply drop out. That cannot create new dependencies, so the order stays valid.
- **Third-party plugins and apps** add their own entities. Rebuild from that instance's schema (see below). New entities that match no package rule land in the catch-all package "Grundlagen (System)".
- **Versions:** minor updates occasionally add fields or tables; rebuild after a major update.
- **Derived vs. decided:** fields, foreign keys and required flags come straight from the schema. The package boundaries and the list of IDs-in-JSON references are a hand-made proposal, not an official classification. The only guarantee is that no mandatory reference points to a later package.
- **Not included:** unique constraints, unsigned and column lengths. These live in the database, not in the API schema.

## Rebuild for another instance

Requires Python 3.9+, no extra packages. You need Admin API access to the shop (an integration, or an admin user).

```bash
# 1. fetch schema + version (credentials only via environment, nothing is stored)
export SW_URL=https://shop.example.com
export SW_CLIENT_ID=...        # integration access key ID
export SW_CLIENT_SECRET=...    # integration secret
export SW_LABEL="Customer X staging"   # optional, shown on the page
python3 fetch_schema.py

# 2. compute packages and dependencies, check the load order
python3 build.py

# 3. render the page
python3 build_page.py          # -> index.html
```

To use an admin user instead of an integration, set `SW_GRANT=password` and put username and password into `SW_CLIENT_ID` / `SW_CLIENT_SECRET`.

You can also fetch the schema by hand: `GET /api/_info/entity-schema.json` with an Admin API token, saved as `entity-schema.json`.

## Files

| File | Purpose |
|---|---|
| `index.html` | The generated page (snapshot 6.7.13.0) |
| `entity-schema.json` | Entity schema of the snapshot instance, as returned by the Admin API |
| `version.json` | Shopware version and label shown on the page |
| `fetch_schema.py` | Fetches schema and version from an instance |
| `build.py` | Package rules (`PKG_RULES`), package order (`PKGS`), hand-maintained JSON references (`SOFT`); writes `model.json` |
| `build_page.py` | Renders `index.html` from `page.tpl.html` |
| `page.tpl.html` | Page template (HTML, CSS, JS) |

## Adjusting the package cut

Edit `PKG_RULES` (regex per package, first match wins) and `PKGS` (load order) in `build.py`. After each run, check that `build.py` reports no backward mandatory references; if it does, move the entity named in the output to a later package or reorder the packages.
