#include <riscv/mmio_plugin.h>
#include <stdio.h>
#include <stdlib.h>

enum {
    FINISHER_FAIL = 0x3333,
    FINISHER_PASS = 0x5555
};

void* test_plugin_alloc(const char* args) {
	return NULL;
}

bool test_plugin_load(void* self, reg_t addr, size_t len, uint8_t* bytes) {
	return true;
}

bool test_plugin_store(void* self, reg_t addr, size_t len, const uint8_t* bytes) {
	uint32_t value = (uint32_t)bytes[3] << 24 |
	                 (uint32_t)bytes[2] << 16 |
                     (uint32_t)bytes[1] << 8  |
                     (uint32_t)bytes[0];
	
	uint16_t status = value & 0xffff;
    uint16_t code = (value >> 16) & 0xffff;

	switch (status) {
        case FINISHER_FAIL:
            exit(code);
        case FINISHER_PASS:
            exit(0);
        default:
            break;
    }

	return true;
}

void test_plugin_dealloc(void* self) {
}

__attribute__((constructor)) static void on_load()
{
  static mmio_plugin_t test_plugin = {
	  test_plugin_alloc,
	  test_plugin_load,
	  test_plugin_store,
	  test_plugin_dealloc
  };

  register_mmio_plugin("test_plugin", &test_plugin);
}
