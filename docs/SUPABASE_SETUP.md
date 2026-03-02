# Supabase Integration Setup

The InvestIQ application now uses Supabase as the primary database for portfolio and watchlist data.

## Environment Variables

Set these environment variables in your deployment platform (Vercel, Heroku, etc.):

```bash
SUPABASE_URL=https://jvgxgfbthfsdqtvzeuqz.supabase.co
SUPABASE_KEY=<your_supabase_secret_key>
```

For local development, copy `.env.example` to `.env` and fill in the values.

## Database Schema

The following tables are used:

### baskets
- `id` (serial, primary key)
- `name` (text)
- `icon` (text)
- `weight` (text)
- `sort_order` (integer)
- `created_at` (timestamp)

### holdings
- `id` (serial, primary key)
- `basket_id` (integer, foreign key → baskets)
- `ticker` (text)
- `position_pct` (numeric)
- `created_at` (timestamp)
- Unique constraint: (basket_id, ticker)

### watchlist_entries
- `id` (serial, primary key)
- `ticker` (text, unique)
- `added_date` (text)
- `entry_price` (numeric)
- `snapshot` (jsonb)
- `created_at` (timestamp)

## Fallback Behavior

If Supabase is unavailable, the application will fall back to local JSON files:
- `data/portfolio.json`
- `data/watchlist_entries.json`

This ensures the application continues to work even if the database is down.

## API Endpoints

The following endpoints now use Supabase:
- `GET /api/portfolio` - Fetch portfolio from Supabase
- `POST /api/portfolio` - Save portfolio to Supabase
- `GET /api/watchlist_entries` - Fetch watchlist entries
- `POST /api/watchlist_entries` - Save watchlist entries

## Testing

Test the integration:
```bash
# Test portfolio read
python3 -c "from app import app; c=app.test_client(); r=c.get('/api/portfolio'); print(r.json.keys()); print(len(r.json['baskets']), 'baskets')"

# Test watchlist read
python3 -c "from app import app; c=app.test_client(); r=c.get('/api/watchlist_entries'); print(r.json)"

# Test generate_watchlist still works
python3 generate_watchlist.py
```

## Deployment Notes

### Vercel
1. Go to your project settings → Environment Variables
2. Add `SUPABASE_URL` and `SUPABASE_KEY`
3. Redeploy

The application will automatically use these environment variables.
