include .env.make

update:
	rsync -av --delete --rsh='ssh -o StrictHostKeyChecking=no ' --progress \
		--exclude="__pycache__" \
		--exclude="**.pyc" \
		config/custom_components/* $(DEPLOY_HOST):/config/custom_components/

	$(MAKE) update-config

UNISON_OPTS = -ignorearchives
config_files = \
	configuration.yaml \
	media_player.yaml \
	automations.yaml \
	mqtt.yaml \
	scripts.yaml

update-config:
	$(foreach file,$(config_files), \
		$(call update_merge, config/$(file), /config/$(file)); \
	)

# $(call update_merge, config/configuration.yaml, /config/configuration.yaml)
# $(call update_merge, config/automations.yaml, /config/automations.yaml)


update-config-override:
	$(foreach file,$(config_files), \
		$(call upload, config/$(file), /config/$(file)); \
	)

restart-core:
	$(call ssh, ha core restart)

