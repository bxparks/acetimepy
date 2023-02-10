# Generate the validation report of acetime.acetz.acetz compared to
# zoneinfo.ZoneInfo.

START_YEAR := 1840
UNTIL_YEAR := 2100

zoneinfo_variance.txt: validate_zoneinfo.py
	python3 validate_zoneinfo.py \
		--start_year $(START_YEAR) \
		--until_year $(UNTIL_YEAR) \
		> $@

clean:
	rm -f zoneinfo_variance.txt
