TARGETS := zone_infos.py zone_policies.py zone_registry.py

TZ_VERSION := 2021c
START_YEAR := 1974
UNTIL_YEAR := 2050

TOOLS := $(abspath ../../../../AceTimeTools)

all: $(TARGETS)

.PHONY: $(TARGETS)

zone_infos.py:
	$(TOOLS)/tzcompiler.sh \
		--tag $(TZ_VERSION) \
		--action zonedb \
		--language python \
		--scope extended \
		--start_year $(START_YEAR) \
		--until_year $(UNTIL_YEAR)

zone_policies.py: zone_infos.py

zone_registry.py: zone_infos.py

clean:
	rm -f $(TARGETS)
