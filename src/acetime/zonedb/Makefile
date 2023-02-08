TARGETS := zone_infos.py zone_policies.py zone_registry.py

TOOLS := $(abspath ../../../../AceTimeTools)
TZ_REPO := $(abspath ../../../../tz)
TZ_VERSION := 2022g
START_YEAR := 1974
UNTIL_YEAR := 10000

all: $(TARGETS)

.PHONY: $(TARGETS)

zone_infos.py:
	$(TOOLS)/tzcompiler.sh \
		--tzrepo $(TZ_REPO) \
		--tag $(TZ_VERSION) \
		--action zonedb \
		--language python \
		--scope extended \
		--generate_int16_year \
		--start_year $(START_YEAR) \
		--until_year $(UNTIL_YEAR)

zone_policies.py: zone_infos.py

zone_registry.py: zone_infos.py

clean:
	rm -f $(TARGETS)
