include .env.make

# update:
# 	rsync -av --delete --rsh='ssh -o StrictHostKeyChecking=no ' --progress \
# 		--exclude="__pycache__" \
# 		--exclude="**.pyc" \
# 		config/custom_components/* $(DEPLOY_HOST):/config/custom_components/

# 	$(MAKE) update-config

UNISON_OPTS = -ignorearchives
# 递归包含 config/ 下所有 yaml（含 display/ 等子目录）
config_files = $(patsubst config/%,%,$(shell find config -type f -name '*.yaml' | sort))
# 仅子目录（排除 config/ 顶层），同步前先在远端 mkdir
config_subdirs = $(sort $(patsubst %/,%,$(filter-out ./,$(dir $(config_files)))))

update-config:
	$(if $(config_subdirs),\
		$(call ssh, mkdir -p $(addprefix /config/,\
			$(config_subdirs))))
	$(foreach file,$(config_files), \
		$(call update_merge, config/$(file), /config/$(file)); \
	)


update-config-override:
	$(if $(config_subdirs),$(call ssh, mkdir -p $(addprefix /config/,$(config_subdirs))))
	$(foreach file,$(config_files), \
		$(call upload, config/$(file), /config/$(file)); \
	)

restart-core:
	$(call ssh, ha core restart)
