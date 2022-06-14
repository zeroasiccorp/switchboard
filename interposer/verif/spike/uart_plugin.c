#include <riscv/mmio_plugin.h>
#include <stdio.h>
#include <string.h>

void* uart_plugin_alloc(const char* args) {
	return NULL;
}

bool uart_plugin_load(void* self, reg_t addr, size_t len, uint8_t* bytes) {
	memset(bytes, 0, len);
	return true;
}

bool uart_plugin_store(void* self, reg_t addr, size_t len, const uint8_t* bytes) {
	fwrite(bytes, 1, len, stdout);
	return true;
}

void uart_plugin_dealloc(void* self) {
}

__attribute__((constructor)) static void on_load()
{
  static mmio_plugin_t uart_plugin = {
	  uart_plugin_alloc,
	  uart_plugin_load,
	  uart_plugin_store,
	  uart_plugin_dealloc
  };

  register_mmio_plugin("uart_plugin", &uart_plugin);
}
