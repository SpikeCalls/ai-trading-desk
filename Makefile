.PHONY: test shadow paper stocks review review-claude kill

test:            ## run the offline test suite
	python -m unittest discover -s tests -v

shadow:          ## one full cycle, journal + alerts, no position
	python run_crypto.py --shadow --once

paper:           ## paper trading, every 60 seconds
	python run_crypto.py

stocks:          ## Alpaca paper account, every 15 minutes while open
	python run_stocks.py

review:          ## weekly stats from journal.jsonl
	python review.py

review-claude:   ## weekly stats + a blunt written review
	python review.py --claude

kill:            ## stop the desk on its next cycle
	touch KILL
