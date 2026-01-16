# VNDB Yomitan Dictionary Builder

Build a Yomitan-compatible dictionary from VNDB character data for Japanese visual novels.

## Features

- **Comprehensive Character Data**: Fetches all Japanese VNs and their characters from VNDB
- **Rate Limited**: Respects VNDB's API rate limit (800 requests/hour ≈ 4.5s between requests)
- **Resumable**: Save progress and resume from where you left off
- **Character Images**: Downloads and includes character images in the dictionary
- **Multiple Search Terms**: Creates entries for full names, family names, given names, and honorific variants
- **Spoiler Filtering**: Configure spoiler level (0=None, 1=Minor, 2=Major)
- **Role-Based Scoring**: Prioritizes main characters over side characters in search results

## Requirements

### Python Dependencies

```bash
pip install jaconv pillow
```

- `jaconv`: For converting romanized names to hiragana
- `pillow` (PIL): For image thumbnail generation (optional but recommended)

## Usage

### Basic Usage

Start a fresh build of the dictionary:

```bash
python build_vndb_yomitan_dict.py
```

This will:
1. Fetch all Japanese VN IDs from VNDB
2. For each VN, fetch character data
3. Generate a Yomitan dictionary ZIP file
4. Save progress to `vndb_dict_state.json`

**Note**: This will take a LONG time (possibly days) due to rate limiting and the large number of VNs on VNDB.

### Resume from Previous Run

If the script is interrupted (Ctrl+C) or encounters an error:

```bash
python build_vndb_yomitan_dict.py --resume
```

### Test with Limited Dataset

To test with only 10 VNs:

```bash
python build_vndb_yomitan_dict.py --max-vns 10
```

### Skip Image Downloads

Images make the dictionary larger and slower to build. To skip them:

```bash
python build_vndb_yomitan_dict.py --no-images
```

### Include Spoilers

By default, no spoiler content is included. To include minor spoilers:

```bash
python build_vndb_yomitan_dict.py --spoiler-level 1
```

Spoiler levels:
- `0`: No spoilers (name, image, role only)
- `1`: Minor spoilers (+ filtered description, basic traits)
- `2`: Full spoilers (+ complete description, all traits)

### Export Only

If you've already processed VNs and just want to re-export the dictionary:

```bash
python build_vndb_yomitan_dict.py --export-only
```

### All Options

```bash
python build_vndb_yomitan_dict.py --help
```

```
Options:
  --resume              Resume from previous state
  --force               Force rebuild even if previous run completed
  --max-vns N           Maximum number of VNs to process (default: all)
  --output PATH         Output ZIP file path (default: ./vndb_yomitan_dict.zip)
  --state-file PATH     State file path (default: ./vndb_dict_state.json)
  --no-images           Skip downloading character images (faster)
  --spoiler-level N     Maximum spoiler level: 0=None, 1=Minor, 2=Major
  --export-only         Skip fetching, only export dictionary from saved state
```

## Output

The script generates:
- **vndb_yomitan_dict.zip**: Yomitan dictionary ZIP file
- **vndb_dict_state.json**: State file for resuming

### Importing into Yomitan

1. Open Yomitan settings
2. Go to "Dictionaries" → "Import"
3. Select the generated `vndb_yomitan_dict.zip` file
4. Enable the dictionary

Now when you hover over character names in Japanese text, Yomitan will show:
- Character's romanized and Japanese name
- Character image
- Visual novel they're from
- Role (protagonist, main character, etc.)
- Physical attributes (age, height, etc.)
- Personality traits and character info

## Module Structure

```
yomitan_dict/
├── __init__.py              # Package initialization
├── name_parser.py           # Japanese name parsing and reading generation
├── image_handler.py         # Image decoding and validation
├── content_builder.py       # Yomitan structured content creation
├── dict_builder.py          # Dictionary builder orchestration
├── build_vndb_yomitan_dict.py  # Main script (this is what you run)
└── README.md                # This file
```

### VNDB API Client

The VNDB API client is located at:
```
GameSentenceMiner/util/vndb_api_client.py
```

## How It Works

### 1. Fetch VN IDs

The script first fetches all Japanese VN IDs from VNDB:
- Queries VNDB for VNs where `olang = "ja"`
- Paginates through results (100 per page)
- Saves all IDs to state file

### 2. Process Each VN

For each VN:
1. Fetch VN metadata (title, description)
2. Fetch all characters with pagination
3. Download character images (optional)
4. Process character traits and categorize by spoiler level
5. Add characters to dictionary builder

### 3. Generate Dictionary Entries

For each character, create multiple searchable terms:
- **Full name**: 田中花子 → たなかはなこ
- **Family name**: 田中 → たなか
- **Given name**: 花子 → はなこ
- **Honorifics**: 田中さん, 田中様, 田中先輩, etc.

### 4. Export to ZIP

The dictionary is exported as a ZIP containing:
- `index.json`: Dictionary metadata
- `tag_bank_1.json`: Tag definitions
- `term_bank_N.json`: Term entries (chunked, 10k per file)
- `img/cXXXX.jpg`: Character images

## Rate Limiting

VNDB allows **800 requests per hour**. The script:
- Waits 4.5 seconds between each request
- Saves progress every 10 VNs
- Can be safely interrupted with Ctrl+C

### Time Estimates

With ~100,000 VNs on VNDB:
- **Fetching VN IDs**: ~1,000 pages × 4.5s = ~1.25 hours
- **Processing characters**: Depends on VN count with characters
  - If every VN has characters: ~125 hours (~5 days)
  - Realistically: ~24-72 hours (many VNs have no character data)

## Troubleshooting

### Error: "Module 'jaconv' not found"

Install the required dependency:
```bash
pip install jaconv
```

### Rate limit errors from VNDB

The script should automatically handle rate limiting. If you still get errors:
1. Stop the script
2. Wait 1 hour
3. Resume with `--resume`

### Out of memory

If processing too many characters causes memory issues:
1. Stop the script
2. Export with `--export-only`
3. Clear state and restart in smaller batches using `--max-vns`

### Images not showing in Yomitan

Make sure you:
1. Used `pillow` (PIL) for image thumbnails
2. Didn't use `--no-images` flag
3. VNDB had images available for those characters

## Advanced Usage

### Running in the Background

Use `nohup` or `screen` to run the script in the background:

```bash
# With nohup
nohup python build_vndb_yomitan_dict.py > build.log 2>&1 &

# With screen
screen -S vndb-dict
python build_vndb_yomitan_dict.py
# Detach with Ctrl+A, D
```

### Automated Resume on Failure

Create a wrapper script that auto-resumes:

```bash
#!/bin/bash
while true; do
    python build_vndb_yomitan_dict.py --resume
    if [ $? -eq 0 ]; then
        break
    fi
    echo "Script failed, waiting 60s before retry..."
    sleep 60
done
```

## License

This tool fetches data from VNDB (https://vndb.org) which is licensed under CC BY-NC-SA.
Please respect VNDB's terms of service and attribution requirements.
