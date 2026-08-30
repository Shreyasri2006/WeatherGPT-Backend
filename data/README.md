# Historical weather data

The repository does **not** redistribute the Kaggle dataset discussed in the SIH report.

1. Download your chosen India Daily Weather (2000–2024) dataset from Kaggle.
2. Put the CSV in this folder, for example:

   `data/india_daily_weather.csv`

3. Update `HISTORICAL_DATASET_PATH` in `.env` if the filename differs.
4. Run:

   ```bash
   python scripts/check_dataset.py data/india_daily_weather.csv
   ```

The historical loader attempts to auto-detect city/location, date and maximum-temperature columns. If your dataset uses different names, edit the candidate lists in `app/services/historical.py`.

**Important:** historical/Kaggle data supplies climate context and anomaly analysis. It is not used as tomorrow's live forecast source.
