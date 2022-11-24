#ifndef PCIEDEV_H__
#define PCIEDEV_H__

#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <sys/mman.h>
static inline void *pcie_bar_map(const char *bdf, int bar_num,
				 uint64_t offset, uint64_t size) {
	char name[] = "/sys/bus/pci/devices/XXXX:XX:XX.X/resourceYY";
	void *p = MAP_FAILED;
	int fd = -1;

	snprintf(name, sizeof name,
		 "/sys/bus/pci/devices/%s/resource%d", bdf, bar_num);

	fd = open(name, O_RDWR | O_SYNC);
	if (fd < 0) {
		goto done;
	}

	p = mmap(NULL, size, PROT_READ | PROT_WRITE,
		 MAP_SHARED, fd, offset);

done:
	if (fd > 0) {
		close(fd);
	}
	return p;
}

static inline void pcie_bar_unmap(void *p, uint64_t size) {
	int r;

	r = munmap(p, size);
	if (r < 0) {
		perror("munmap");
	}
}
#endif
