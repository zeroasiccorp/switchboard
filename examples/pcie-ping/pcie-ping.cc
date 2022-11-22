/*
 * Switchboard PCIe ping example.
 *
 * Copyright (C) 2022 Zero ASIC.
 */
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

#include "switchboard.hpp"
#include "spsc_queue.h"
#include "pagemap.h"
#include "pciedev.h"

static void usage(const char *progname) {
	printf("%s: BDF BAR-num offset\n\n", progname);
}

static inline void _bar_write64(void *p, uint64_t val) {
	* (volatile uint64_t *) p = val;
}

static inline void bar_write64(void *p, uint64_t val) {
	uintptr_t i = (uintptr_t) p;

	// Enforce 64-bit aligment.
	assert((i & 7) == 0);

	// Make access.
	_bar_write64(p, val);
}

int main(int argc, char* argv[]) {
	uint64_t tx_phys, rx_phys;
	uint64_t bar_size;
	const char *bdf;
	int capacity;
	int bar_num;
	void *bar_p;
	SBTX tx;
	SBRX rx;
	int r;
	int i;

	if (argc < 2) {
		usage(argv[0]);
		return EXIT_FAILURE;
	}

	bdf = argv[1];
	bar_num = 0;

	// Create queue's that fit into a single page.
	capacity = spsc_capacity(getpagesize());
	tx.init("queue-tx", capacity);
	rx.init("queue-rx", capacity);

	// Lock pages into RAM (avoid ondemand allocation or swapping).
	r = tx.mlock();
	if (r) {
		perror("mlock");
		goto done;
	}
	r = rx.mlock();
	if (r) {
		perror("mlock");
		goto done;
	}

	// Now we've got two single-page queue's with pages locked into memory.
	// Get hold of their physical addresses.
	tx_phys = pagemap_virt_to_phys(tx.get_shm_handle());
	rx_phys = pagemap_virt_to_phys(rx.get_shm_handle());

	printf("tx_phys 0x%" PRIx64 "\n", tx_phys);
	printf("rx_phys 0x%" PRIx64 "\n", rx_phys);

	bar_size = 2 * getpagesize();
	bar_p = pcie_bar_map(bdf, bar_num, 0, bar_size);
	if (bar_p == MAP_FAILED) {
		perror("pcie_map_bar");
		goto done;
	}

	printf("%s: BAR%d mapped at %p\n", bdf, bar_num, bar_p);
	if (1) {
		// Program queue address registers in both queues.
		bar_write64(bar_p, tx_phys);
		bar_write64((char *) bar_p + 4 * 1024, rx_phys);
	}

	for (i = 0; i < 1024; i++) {
		sb_packet p = {0};

		printf("ping %d\n", i);
		while(!tx.send(p))
			;
		while(!rx.recv(p))
			;
	}

	pcie_bar_unmap(bar_p, bar_size);
done:
	delete_shared_queue("queue-tx");
	delete_shared_queue("queue-rx");
	return 0;
}
