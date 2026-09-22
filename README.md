# 卄卂丂卄 ㄥ乇ᗪᎶ乇尺

A public archive that generates and tracks unique hashes used as ID suffixes across projects (e.g. `namedrop-2026-9c8b`, `casepilot-2026-7e2b`).

Each hash is generated once, logged here, and never repeated — this repo is the single source of truth for "has this hash been used before." Supports multiple charsets and lengths, an ambiguous-character filter, optional prefixes/labels, a reserved/blocklist file, and automatic integrity checks.

## Structure

```
hash-ledger/
├── .github/
│   └── workflows/
│       ├── generate-hash.yml   # GitHub Action to generate + commit new hashes
│       └── validate.yml        # GitHub Action to check the archive for duplicates/errors
├── new_hash.py                 # Script that generates hashes and checks for duplicates
├── validate_archive.py         # Script that checks archive integrity
├── hash_archive.csv            # Running log of every hash ever generated
├── reserved.csv                # Optional blocklist of hashes that should never be generated
├── LICENSE                     # MIT license
└── README.md
```

## How it works

- `new_hash.py` generates a random hash using the chosen charset and length (default: 4-character hex, e.g. `048a`, `0c90`, `1b34`)
- Before returning it, it checks `hash_archive.csv` (and `reserved.csv`, if used) to make sure that hash hasn't been used or blocked
- The new hash is appended to `hash_archive.csv` with metadata: when it was created, its length/charset, its status, and an optional label/notes
- `validate_archive.py` runs automatically on every change to `hash_archive.csv`, checking for duplicates, malformed rows, and invalid charset/length/status values

## Archive schema

```csv
hash,created_at,length,charset,status,label,notes
9c8b,2026-09-22T14:03:11Z,4,hex,active,,
```

| Column | Meaning |
|---|---|
| `hash` | The generated value |
| `created_at` | UTC timestamp of generation |
| `length` | Number of characters |
| `charset` | `hex`, `base36`, or `base62` |
| `status` | `active` or `retired` — retire a hash instead of deleting its row |
| `label` | Optional tag, e.g. which project claimed it |
| `notes` | Optional freeform notes |

## Usage — via GitHub Actions

1. Go to the **Actions** tab
2. Select **Generate Hash** on the left
3. Click **Run workflow**
4. Fill in the options (all optional, sensible defaults are pre-filled):
   - **count** — how many hashes to generate (default `1`)
   - **length** — hash length (default `4`)
   - **charset** — `hex`, `base36`, or `base62` (default `hex`)
   - **strict** — exclude ambiguous characters like `0`/`O` or `1`/`l`/`I` (default off)
   - **prefix** — optional prefix shown with the printed hash, e.g. `usr` → `usr-9c8b`
   - **label** — optional tag stored with the hash, e.g. a project name
5. Click **Run workflow** to confirm
6. Wait for the run to finish, refresh — a green checkmark means it ran
7. `hash_archive.csv` now has the new hash(es) committed automatically, and **Validate Archive** runs automatically right after to confirm everything's still consistent

### Get the hash out
- Either open `hash_archive.csv` in the repo and copy the last row
- Or click into the finished workflow run → the **"Generate hash(es)"** step → it prints the new hash(es) directly in the log

## Usage — locally (optional)

```bash
git clone git@github.com:yourname/hash-ledger.git
cd hash-ledger

# generate one 4-char hex hash
python3 new_hash.py

# generate multiple at once
python3 new_hash.py --count 5

# a longer, letter-safe base36 hash
python3 new_hash.py --length 6 --charset base36 --strict

# with a prefix and label
python3 new_hash.py --prefix usr --label "namedrop"

# check the archive is still valid
python3 validate_archive.py

# push the updated archive back
git add hash_archive.csv
git commit -m "add new hash(es)"
git push
```

## Reserved hashes

Add any hash you want permanently excluded from generation to `reserved.csv`:

```csv
hash
dead
0000
```

> [!NOTE]
> `hash_archive.csv` is only ever appended to by the workflow — don't hand-edit existing rows unless retiring a hash you know was never actually used (set its `status` to `retired` rather than deleting the row).
