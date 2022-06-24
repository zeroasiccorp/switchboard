#include <riscv/mmio_plugin.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include "common.h"

void* exit_plugin_alloc(const char* args) {
	return NULL;
}

bool exit_plugin_load(void* self, reg_t addr, size_t len, uint8_t* bytes) {
	return true;
}

bool exit_plugin_store(void* self, reg_t addr, size_t len, const uint8_t* bytes) {
	uint32_t value = (uint32_t)bytes[3] << 24 |
	                 (uint32_t)bytes[2] << 16 |
	                 (uint32_t)bytes[1] << 8  |
	                 (uint32_t)bytes[0];
	
	uint16_t status = value & 0xffff;
	uint16_t code = (value >> 16) & 0xffff;

	switch (status) {
		case EXIT_FAIL: exit(code);
		case EXIT_PASS: exit(0);
		default:
			fprintf(stderr,"Unknown Core Exit Status");
			break;
	}

	return true;
}

void exit_plugin_dealloc(void* self) {
}

__attribute__((constructor)) static void on_load()
{
	static mmio_plugin_t exit_plugin = {
		exit_plugin_alloc,
		exit_plugin_load,
		exit_plugin_store,
		exit_plugin_dealloc
	};

	register_mmio_plugin("exit_plugin", &exit_plugin);
}
