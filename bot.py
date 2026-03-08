name: onlyfans-monitor

on:
  schedule:
    - cron: "*/30 * * * *"
  workflow_dispatch:

jobs:
  run:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Install Playwright browsers
        run: playwright install --with-deps

      - name: Run bot
        run: python bot.py

      - name: Commit updated counter
        run: |
          git config --global user.name "bot"
          git config --global user.email "bot@users.noreply.github.com"
          git add count.json
          git commit -m "update counter" || echo "no changes"
          git push