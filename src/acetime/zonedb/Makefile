TARGETS := zone_infos.py zone_policies.py zone_registry.py

TOOLS := $(abspath ../../../../AceTimeTools)
TZ_REPO := $(abspath ../../../../tz)
TZ_VERSION := 2024a
START_YEAR := 2000
UNTIL_YEAR := 2200

all: $(TARGETS)

.PHONY: $(TARGETS)

zone_infos.py:
	$(TOOLS)/tzcompiler.sh \
		--tzrepo $(TZ_REPO) \
		--tag $(TZ_VERSION) \
		--actions zonedb \
		--languages python \
		--scope complete \
		--skip_bufestimator \
		--start_year $(START_YEAR) \
		--until_year $(UNTIL_YEAR)

zone_policies.py: zone_infos.py

zone_registry.py: zone_infos.py

clean:
	rm -f $(TARGETS)
