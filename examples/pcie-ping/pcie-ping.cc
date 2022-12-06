/*
 * Switchboard PCIe ping example.
 *
 * Copyright (C) 2022 Zero ASIC.
 */
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

#include "switchboard_pcie.hpp"

static void usage(const char *progname) {
	printf("%s: BDF BAR-num offset\n\n", progname);
}

int main(int argc, char* argv[]) {
	const char *bdf;
	int bar_num;
	SBTX_pcie tx;
	SBRX_pcie rx;
	int i;

	if (argc < 2) {
		usage(argv[0]);
		return EXIT_FAILURE;
	}

	bdf = argv[1];
	bar_num = 0;

	tx.init("queue-tx", bdf, bar_num, 0);
	rx.init("queue-rx", bdf, bar_num, 1);

	for (i = 0; i < 1024; i++) {
		sb_packet p = {0};

		printf("ping %d\n", i);
		while(!tx.send(p))
			;
		while(!rx.recv(p))
			;
	}

	delete_shared_queue("queue-tx");
	delete_shared_queue("queue-rx");
	return 0;
}
